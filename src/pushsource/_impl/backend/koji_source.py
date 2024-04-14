import os
import threading
import logging
from functools import partial
import json

from queue import Queue, Empty
from threading import Thread

import koji
from more_executors import Executors
from more_executors.futures import f_map

from ..source import Source
from ..model import (
    KojiBuildInfo,
    RpmPushItem,
    ModuleMdPushItem,
    ModuleMdSourcePushItem,
    OperatorManifestPushItem,
    ContainerImagePushItem,
    SourceContainerImagePushItem,
    VMIPushItem,
    AmiPushItem,
    VHDPushItem,
    BootMode,
)
from ..helpers import (
    list_argument,
    try_int,
    as_completed_with_timeout_reset,
    wait_exist,
)
from .modulemd import Module
from .koji_containers import ContainerArchiveHelper, MIME_TYPE_MANIFEST_LIST

LOG = logging.getLogger("pushsource")
CACHE_LOCK = threading.RLock()

# Arguments used for retry policy.
# Provided so it can be overridden from tests to reduce time spent on retries.
RETRY_ARGS = {}


class ListArchivesCommand(object):
    def __init__(self, build):
        self.build = build
        self.call = None

    def execute(self, source, session):
        archives_cache = source._cache.setdefault("archives", {})
        ident = self.build["id"]
        if ident in archives_cache:
            return 0

        LOG.debug("Get koji archives %s", ident)
        self.call = session.listArchives(ident)
        return 1

    def save(self, source, _):
        if self.call is not None:
            source._cache["archives"][self.build["id"]] = self.call.result
            source._cache["archives"][self.build["nvr"]] = self.call.result


class GetBuildCommand(object):
    def __init__(self, ident, list_archives=False):
        self.ident = ident
        self.list_archives = list_archives
        self.call = None

    def execute(self, source, session):
        build_cache = source._cache.setdefault("build", {})
        if self.ident in build_cache:
            return 0
        LOG.debug("Get koji build %s", self.ident)
        self.call = session.getBuild(self.ident)
        return 1

    def save(self, source, koji_queue):
        if self.call is None:
            build = source._cache["build"][self.ident]
        else:
            # Build is saved under both NVR and ID
            build = self.call.result
            if build:
                source._cache["build"][build["id"]] = build
                source._cache["build"][build["nvr"]] = build
            else:
                source._cache["build"][self.ident] = build
        if self.list_archives and build:
            koji_queue.put(ListArchivesCommand(build))


class GetRpmCommand(object):
    def __init__(self, ident):
        self.ident = ident
        self.call = None

    def execute(self, source, session):
        rpm_cache = source._cache.setdefault("rpm", {})
        if self.ident in rpm_cache:
            return 0
        LOG.debug("Get koji RPM %s", self.ident)
        self.call = session.getRPM(self.ident)
        return 1

    def save(self, source, koji_queue):
        if self.call is not None:
            source._cache["rpm"][self.ident] = self.call.result
        # We have to get the RPM's build as well.
        if source._cache["rpm"][self.ident]:
            build_id = source._cache["rpm"][self.ident]["build_id"]
            koji_queue.put(GetBuildCommand(build_id))


class KojiSource(Source):
    """Uses koji artifacts as the source of push items."""

    _BATCH_SIZE = int(os.environ.get("PUSHSOURCE_KOJI_BATCH_SIZE", "100"))

    def __init__(
        self,
        url,
        dest=None,
        rpm=None,
        module_build=None,
        module_filter_filename=None,
        container_build=None,
        vmi_build=None,
        signing_key=None,
        basedir=None,
        threads=4,
        timeout=60 * 30,
        cache=None,
        executor=None,
    ):
        """Create a new source.

        Parameters:
            url (str)
                URL of the XML-RPC endpoint for koji hub.

            dest (str, list[str])
                The destination(s) to fill in for push items created by this
                source. If omitted, all push items have empty destinations.

            rpm (list[str, int])
                RPM identifier(s). Can be koji IDs (integers) or filenames.
                The source will yield all RPMs identified by this list.

            module_build (list[str, int])
                Build identifier(s). Can be koji IDs (integers) or build NVRs.
                The source will yield modulemd files belonging to these
                build(s), filtered by ``module_filter_filename`` (if given).

            module_filter_filename (list[str])
                Filename(s) of modulemd archives to include in output.

                When ``module_build`` is given, modulemd files are located as
                koji archives with names of the form ``modulemd.<arch>.txt``.
                By default, all of these archives will be processed.

                Providing a non-empty list for ``module_filter_filename`` will
                instead only process modulemd files with those filenames. This
                can be used to select only certain arches.

                Has no effect if ``module_build`` is not provided.

            container_build (list[str, int])
                Build identifier(s). Can be koji IDs (integers) or build NVRs.
                The source will yield all container images produced by these
                build(s), along with associated artifacts such as operator manifest
                bundles.

            vmi_build (list[str, int])
                Virtual Machine Image identifier(s). Can be koji build IDs (integers)
                or build NVRs.
                The source will yield all VMIs identified by this list.

            signing_key (list[str])
                GPG signing key ID(s). If provided, content must be signed
                using one of the provided keys. Include ``None`` if unsigned
                should also be permitted.

                Keys should be listed in the order of preference.

            basedir (str)
                Base directory of koji content (e.g. /mnt/koji).
                This directory must be readable locally.

            threads (int)
                Number of threads used for concurrent queries to koji.

            timeout (int)
                Number of seconds after which an error is raised, if no progress is
                made during queries to koji.

            cache (dict)
                A cache used to retain the results of XML-RPC calls, to avoid
                repeated calls.

                Providing a cache only gives a benefit if the current process
                will create more than a single instance of KojiSource. In this
                case, some calls may be avoided by passing the same cache
                to each instance.

            executor (concurrent.futures.Executor)
                A custom executor used to submit calls to koji.
        """
        self._url = url
        self._rpm = [try_int(x) for x in list_argument(rpm)]
        self._module_build = [try_int(x) for x in list_argument(module_build)]
        self._module_filter_filename = list_argument(
            module_filter_filename, retain_none=True
        )
        self._container_build = [try_int(x) for x in list_argument(container_build)]
        self._vmi_build = [try_int(x) for x in list_argument(vmi_build)]
        self._signing_key = list_argument(signing_key)
        self._dest = list_argument(dest)
        self._timeout = timeout
        self._pathinfo = koji.PathInfo(basedir)
        self._cache = {} if cache is None else cache
        self._threads = threads
        self._executor = (
            executor
            or Executors.thread_pool(name="pushsource-koji", max_workers=threads)
            .with_retry(**RETRY_ARGS)
            .with_cancel_on_shutdown()
        )

        self._on_shutdown = []
        if not executor:
            self._on_shutdown.append(lambda: self._executor.shutdown(True))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for cb in self._on_shutdown:
            cb()

    @property
    def _koji_session(self):
        # A koji client session.
        # Each thread uses a separate client.
        with CACHE_LOCK:
            tls = self._cache.setdefault("tls", threading.local())
            if not hasattr(tls, "koji_session"):
                LOG.debug("Creating koji session: %s", self._url)
                tls.koji_session = koji.ClientSession(self._url)
        return tls.koji_session

    def _koji_check(self):
        # Do a basic connection check with koji.
        # If this succeeds, we can be reasonably sure that the koji connection is
        # more or less working.
        try:
            version = self._executor.submit(self._koji_get_version).result()
        except Exception as ex:  # pylint: disable=broad-except
            msg = "Communication error with koji at %s" % self._url
            raise RuntimeError(msg) from ex

        LOG.debug("Connected to koji %s at %s", version, self._url)

    def _koji_get_version(self):
        with CACHE_LOCK:
            if "koji_version" not in self._cache:
                self._cache["koji_version"] = self._koji_session.getKojiVersion()
            return self._cache["koji_version"]

    def _get_rpm(self, rpm):
        return self._cache["rpm"][rpm]

    def _get_build(self, build_id):
        return self._cache["build"][build_id]

    def _get_archives(self, build_id):
        return self._cache["archives"][build_id]

    def _push_items_from_rpm_meta(self, rpm, meta):
        LOG.debug("RPM metadata for %s: %s", rpm, meta)

        notfound = [RpmPushItem(name=str(rpm), dest=self._dest, state="NOTFOUND")]

        if not meta:
            LOG.error("RPM not found in koji: %s", rpm)
            return notfound

        build = self._get_build(meta["build_id"])
        build_path = self._pathinfo.build(build)
        rpm_path = None
        unsigned_path = os.path.join(build_path, self._pathinfo.rpm(meta))
        rpm_signing_key = None

        candidate_paths = []

        timeout = int(os.getenv("PUSHSOURCE_SRC_POLL_TIMEOUT") or "0")
        poll_rate = int(os.getenv("PUSHSOURCE_SRC_POLL_RATE") or "30")

        # If signing keys requested, try them in order of preference
        # We will wait up to timeout for the highest-priority key to appear
        # If it fails to appear, try keys with lowering priorities until one is present
        key = self._signing_key[0] if self._signing_key else None
        if key:
            key = key.lower()
            candidate = os.path.join(build_path, self._pathinfo.signed(meta, key))
        else:
            candidate = unsigned_path

        wait_exist(candidate, timeout, poll_rate)

        # If signing keys requested, try them in order of preference
        # Some key should be present at this stage, let's try them all
        for key in self._signing_key:
            if key:
                key = key.lower()
                candidate = os.path.join(build_path, self._pathinfo.signed(meta, key))
            else:
                candidate = unsigned_path
            candidate_paths.append(candidate)
            if os.path.exists(candidate):
                rpm_path = candidate
                rpm_signing_key = key
                break

        if self._signing_key:
            # If signing keys requested: we either found an RPM above, or an error occurs
            if not rpm_path:
                LOG.error(
                    "RPM not found in koji at path(s): %s", ", ".join(candidate_paths)
                )
                return notfound
        else:
            # If no signing key requested, we just use the calculated path directly
            # and don't even test for its existence. Note: absence of test for existence
            # is ported from old code and is not necessarily the best way.
            rpm_path = unsigned_path

        return [
            RpmPushItem(
                name=os.path.basename(rpm_path),
                src=rpm_path,
                dest=self._dest,
                signing_key=rpm_signing_key,
                build=build["nvr"],
            )
        ]

    def _module_filtered(self, file_path):
        ok_names = self._module_filter_filename
        filename = os.path.basename(file_path)
        if ok_names is not None and filename not in ok_names:
            LOG.debug("Skipping module %s due to module_filter_filename", file_path)
            return True

        return False

    def _get_module_name(self, nvr, file_path):
        # Return the best value for "name" we can calculate for a given modulemd
        # push item. In practice this means setting the push item name to NSVCA,
        # if the modulemd file exists and can be parsed as a single module.
        # NSVCA is a more meaningful name for the item than modulemd.<arch>.txt,
        # which will be the same for all modules of the same arch.
        #
        # Why only "if the modulemd file exists"? Well, it's only going to exist
        # if the caller has mounted the NFS volume associated with koji. This will
        # be true in production, and we could give a fatal error when this is not
        # the case, but it seems like a very harsh requirement. e.g. most of the
        # docs for this library are using fedora koji as an example, but nobody
        # running outside of fedora infra will be able to mount that volume,
        # meaning attempting to use the examples will immediately hit a brick wall.
        #
        # So, this is a compromise. If the file exists, it has to be valid, and we
        # use it; this gives the best behavior in production. If the file doesn't
        # exist, that's OK, and that's a compromise to avoid making the dev and test
        # requirements too onerous.
        basename = os.path.basename(file_path)

        if basename == "modulemd.src.txt":
            # These are modulemd packager files and not the built files with NSVCA,
            # do not attempt to parse
            return basename

        if not os.path.exists(file_path):
            # Don't have the file, don't attempt to parse
            return basename

        try:
            return Module.from_file(file_path).nsvca
        except:
            # If we fail, make it clear what we were attempting to do before raising
            LOG.exception(
                "In koji build %s, cannot load module metadata from %s", nvr, file_path
            )
            raise

    def _push_items_from_module_build(self, nvr, meta):
        LOG.debug("Looking for modulemd on %s, %s", nvr, meta)

        if not meta:
            message = "Module build not found in koji: %s" % nvr
            LOG.debug(message)
            raise ValueError(message)

        build_id = meta["id"]
        archives = self._get_archives(build_id)
        modules = [elem for elem in archives if elem.get("btype") == "module"]

        out = []
        for module in modules:
            file_path = os.path.join(
                self._pathinfo.typedir(meta, "module"), module["filename"]
            )

            if self._module_filtered(file_path):
                continue

            name = self._get_module_name(nvr, file_path)

            klass = ModuleMdPushItem
            if os.path.basename(file_path) == "modulemd.src.txt":
                klass = ModuleMdSourcePushItem

            out.append(
                klass(name=name, src=file_path, dest=self._dest, build=meta["nvr"])
            )
        return out

    def _push_items_from_container_build(self, nvr, meta):
        LOG.debug("Looking for container images on %s, %s", nvr, meta)

        if not meta:
            message = "Container image build not found in koji: %s" % nvr
            LOG.debug(message)
            raise ValueError(message)

        # The metadata we are interested in is documented here:
        # https://github.com/containerbuildsystem/atomic-reactor/blob/061d92e63cf27ae030e8ceed388ec34f51afb17b/docs/koji.md#type-specific-metadata
        extra = meta.get("extra") or {}
        typeinfo = extra.get("typeinfo") or {}
        # Per above doc, it is preferred to use the metadata under 'typeinfo' if present
        image = typeinfo.get("image") or extra.get("image")

        if image is None:
            message = "Build %s not recognized as a container image build" % nvr
            LOG.debug(message)
            raise ValueError(message)

        build_id = meta["id"]

        archives = self._get_archives(build_id)

        image_archives = [
            elem
            for elem in archives
            if elem.get("btype") == "image" and elem.get("type_name") == "tar"
        ]

        media_types = image.get("media_types") or []
        if MIME_TYPE_MANIFEST_LIST in media_types:
            # in manifest list case it is OK to have multiple archives (different arches).
            pass
        elif len(image_archives) != 1:
            # If we don't have a manifest list, we expect to have an image for one arch.
            # If there's not exactly one, it's unclear what's going on and we'd better halt.
            message = (
                "Could not find (exactly) one container image archive on koji build %s"
                % nvr
            )
            LOG.debug(message)
            raise ValueError(message)

        out = []

        for archive in image_archives:
            helper = ContainerArchiveHelper(meta, archive)

            klass = ContainerImagePushItem
            if image.get("sources_for_nvr"):
                # This is a source image.
                klass = SourceContainerImagePushItem

            out.append(
                klass(
                    # TODO: name might be changed once we start parsing
                    # the metadata from atomic-reactor.
                    name=archive["filename"],
                    dest=self._dest,
                    build=nvr,
                    # Note, we should be able to use the default KojiBuild
                    # construction from NVR here. The reason we don't is that
                    # there is some "impossible" test data in Pub which has
                    # brew builds whose NVR does not match their (n, v, r)
                    # in the build data and it's quite tough to fix that now.
                    build_info=KojiBuildInfo(
                        id=int(build_id),
                        name=meta["name"],
                        version=meta["version"],
                        release=meta["release"],
                    ),
                    source_tags=helper.source_tags,
                    labels=helper.labels,
                    arch=helper.arch,
                    pull_info=helper.pull_info,
                )
            )

        # If this build had any operator-manifests archive, add that too.
        operator = self._get_operator_item(nvr, meta, archives, out)
        if operator:
            out.append(operator)

        return out

    def _push_items_from_vmi_build(self, nvr, meta):
        LOG.debug("Looking for virtual machine images on %s, %s", nvr, meta)

        if not meta:
            message = "Virtual machine image build not found in koji: %s" % nvr
            LOG.debug(message)
            raise ValueError(message)

        # VMI has the {'typeinfo': {'image':{}}} on extra
        extra = meta.get("extra") or {}
        typeinfo = extra.get("typeinfo") or {}
        image = typeinfo.get("image")

        # Container images have the key `container_koji_task_id` set on extras:
        # https://github.com/containerbuildsystem/atomic-reactor/blob/master/docs/koji.md?plain=1#L79
        if extra.get("container_koji_task_id"):
            message = "The build %s is for container images." % nvr
            LOG.debug(message)
            raise ValueError(message)

        if image is None:
            message = "Build %s not recognized as a virtual machine image build" % nvr
            LOG.debug(message)
            raise ValueError(message)

        build_id = meta["id"]
        archives = self._get_archives(build_id)
        for archive in archives:
            if archive["filename"] == "meta.json":
                return self._push_items_from_rhcos_build(nvr, meta)

        # Supported types of VMI archives
        ami_types = ["raw", "raw-xz"]
        azure_types = ["vhd", "vhd-compressed"]
        cloud_types = {}

        for k in ami_types:
            cloud_types.setdefault(k, AmiPushItem)

        for k in azure_types:
            cloud_types.setdefault(k, VHDPushItem)

        # Collect all known VM image archives
        vmi_archives = [
            elem
            for elem in archives
            if elem.get("btype") == "image"
            and elem.get("type_name") in cloud_types.keys()
        ]
        out = []
        # Generate the respective PushItem type for each archive
        for archive in vmi_archives:
            path = self._pathinfo.typedir(meta, archive["btype"])
            item_src = os.path.join(path, archive["filename"])

            extra = archive.get("extra") or {}
            image = extra.get("image") or {}
            arch = image.get("arch")
            boot_mode = image.get("boot_mode")
            if boot_mode is not None:
                boot_mode = BootMode(boot_mode)

            klass = cloud_types.get(archive["type_name"]) or VMIPushItem

            rel_klass = klass._RELEASE_TYPE

            # The given name will be composed by the product name and cloud
            # marketpalce name, like "rhel-azure" or "rhel-sap-azure".
            # We just want to get the product name without the cloud name,
            # like "rhel" and "rhel-sap" in our examples respectively.
            splitted_name = meta["name"].split("-")
            if len(splitted_name) > 1:
                product = "-".join(splitted_name[:-1])
            else:
                product = splitted_name[0]

            # Try to get the resping version from release, if available
            respin = try_int(meta["release"])
            respin = 0 if not isinstance(respin, int) else respin

            release = rel_klass(
                arch=arch,
                date=(meta.get("completion_time") or "").split(" ")[0],
                product=product.upper(),
                version=meta["version"],
                respin=respin,
            )

            out.append(
                klass(
                    name=archive["filename"],
                    description="",
                    dest=self._dest,
                    src=item_src,
                    boot_mode=boot_mode,
                    build=nvr,
                    build_info=KojiBuildInfo(
                        id=int(build_id),
                        name=meta["name"],
                        version=meta["version"],
                        release=meta["release"],
                    ),
                    md5sum=archive.get("checksum"),
                    release=release,
                )
            )

        return out

    def _push_items_from_rhcos_build(self, nvr, meta, archives=None):

        LOG.debug("Looking for core os assembler build on %s, %s", nvr, meta)

        build_id = meta["id"]
        archives = archives or self._get_archives(build_id)

        for archive in archives:
            if archive.get("filename") == "meta.json":
                path = self._pathinfo.typedir(meta, archive["btype"])
                item_src = os.path.join(path, archive["filename"])
                with open(item_src) as archive_file:
                    rhcos_meta_data = json.loads(archive_file.read())

        extra = meta.get("extra") or {}
        image = extra.get("typeinfo").get("image") or {}

        arch = image.get("arch")

        boot_mode = image.get("boot_mode")
        if boot_mode is not None:
            boot_mode = BootMode(boot_mode)

        rhcos_container_config = (
            rhcos_meta_data.get("coreos-assembler.container-config-git") or {}
        )
        branch = rhcos_container_config.get("branch") or ""
        version = branch.split("-")[-1] or ""

        # Try to get the resping version from release, if available
        respin = try_int(meta["release"])
        respin = 0 if not isinstance(respin, int) else respin

        vms_with_custom_meta_data = []
        # add aws ami
        for ami in rhcos_meta_data["amis"]:
            vms_with_custom_meta_data.append(
                {
                    "marketplace_name": "aws",
                    "push_item_class": AmiPushItem,
                    "custom_meta_data": {
                        "region": ami.get("name"),
                        "src": ami.get("hvm"),
                    },
                }
            )

        # add vm for azure
        vms_with_custom_meta_data.append(
            {
                "marketplace_name": "azure",
                "push_item_class": VHDPushItem,
                "custom_meta_data": {
                    "src": rhcos_meta_data["azure"]["url"],
                },
            }
        )

        out = []
        for vm_item in vms_with_custom_meta_data:
            klass = vm_item.get("push_item_class")
            rel_klass = klass._RELEASE_TYPE
            release = rel_klass(
                arch=arch,
                date=(meta.get("completion_time") or "").split(" ")[0],
                product=meta.get("name").split("-")[0].upper(),
                version=version,
                respin=respin,
            )
            images = rhcos_meta_data.get("images") or {}
            vm_target = images.get(vm_item["marketplace_name"]) or {}
            sha256sum = vm_target.get("sha256")

            out.append(
                klass(
                    name=rhcos_meta_data.get("name"),
                    description=rhcos_meta_data.get("summary"),
                    **vm_item["custom_meta_data"],
                    boot_mode=boot_mode,
                    build=nvr,
                    build_info=KojiBuildInfo(
                        id=int(build_id),
                        name=meta["name"],
                        version=version,
                        release=meta["release"],
                    ),
                    sha256sum=sha256sum,
                    release=release,
                    marketplace_name=vm_item["marketplace_name"]
                )
            )

        return out

    def _get_operator_item(self, nvr, meta, archives, container_items):
        extra = meta.get("extra") or {}
        typeinfo = extra.get("typeinfo") or {}
        operator_manifests = typeinfo.get("operator-manifests") or {}
        operator_archive_name = operator_manifests.get("archive")
        image = typeinfo.get("image") or {}
        image_operator_manifests = image.get("operator_manifests") or {}
        related_images = image_operator_manifests.get("related_images") or {}
        pullspecs = related_images.get("pullspecs") or []
        operator_related_images = [spec["new"] for spec in pullspecs if spec.get("new")]

        if not operator_archive_name:
            # Try legacy form
            operator_archive_name = extra.get("operator_manifests_archive")

        if not operator_archive_name:
            # No operator manifests on this build
            return

        operator_archive = [
            a for a in archives if a["filename"] == operator_archive_name
        ]
        if len(operator_archive) != 1:
            message = (
                "koji build %s metadata refers to missing operator-manifests "
                'archive "%s"'
            ) % (nvr, operator_archive_name)
            raise ValueError(message)

        return OperatorManifestPushItem(
            name=os.path.join(nvr, operator_archive_name),
            dest=self._dest,
            build=nvr,
            related_images=operator_related_images,
            container_image_items=container_items,
        )

    def _rpm_futures(self):
        # Get info from each requested RPM.
        rpm_fs = [(self._executor.submit(self._get_rpm, rpm), rpm) for rpm in self._rpm]

        # Convert them to lists of push items
        return [
            f_map(f, partial(self._push_items_from_rpm_meta, rpm)) for f, rpm in rpm_fs
        ]

    def _modulemd_futures(self):
        # Get info from each requested module build.
        module_build_fs = [
            (self._executor.submit(self._get_build, build), build)
            for build in self._module_build
        ]

        # Convert them to lists of push items
        return [
            f_map(f, partial(self._push_items_from_module_build, build))
            for f, build in module_build_fs
        ]

    def _container_futures(self):
        # Get info from each requested container build.
        build_fs = [
            (self._executor.submit(self._get_build, build), build)
            for build in self._container_build
        ]

        # Convert them to lists of push items
        return [
            f_map(f, partial(self._push_items_from_container_build, build))
            for f, build in build_fs
        ]

    def _vmi_futures(self):
        # Get info from each requested virtual machine image build.
        vmi_build_fs = [
            (self._executor.submit(self._get_build, build), build)
            for build in self._vmi_build
        ]

        # Convert them to lists of push items
        return [
            f_map(f, partial(self._push_items_from_vmi_build, build))
            for f, build in vmi_build_fs
        ]

    def _do_fetch(self, koji_queue, exceptions):
        try:
            done = False

            while not done:
                count = 0
                pending_commands = []

                session = self._koji_session.multicall(
                    strict=True, batch=self._BATCH_SIZE
                )

                while not done:
                    try:
                        command = koji_queue.get_nowait()
                        count += command.execute(self, session)
                        pending_commands.append(command)
                    except Empty:
                        done = True
                        LOG.debug("koji fetch queue emptied")

                LOG.debug("koji multicall: about to execute %s call(s)", count)

                session.call_all()

                LOG.debug("koji multicall: executed %s call(s)", count)

                # multicall is now done.
                # Save the result to cache from each command.
                # This could potentially result in new queue entries.
                for command in pending_commands:
                    command.save(self, koji_queue)

                # If there were any commands processed, queue might no longer be
                # empty, so re-check it
                if pending_commands:
                    done = False
        except Exception as e:
            LOG.exception("Error during koji fetches")
            exceptions.append(e)
            raise

    def __iter__(self):
        # Try a (blocking) call to koji before anything else.
        #
        # The reasons for this are:
        #
        # - give an error which is hopefully easier to understand if the
        #   koji connection is completely broken (e.g. caller provides bogus
        #   URL)
        #
        # - work around pyasn1 bug https://github.com/etingof/pyasn1/issues/53
        #   which affects some (ancient) environments. That thread-safety bug
        #   can cause parsing of subjectAltName to fail if it first occurs from
        #   multiple threads simultaneously. Doing a warm-up from one thread
        #   before we spawn multiple threads is a way to avoid this.
        #
        self._koji_check()

        # Queue holding all requests we need to make to koji.
        # We try to fetch as much as we can early to make efficient use
        # of multicall.
        koji_queue = Queue()

        # We'll need to obtain all RPMs referenced by filename
        for rpm_filename in self._rpm:
            koji_queue.put(GetRpmCommand(ident=rpm_filename))

        # We'll need to obtain all builds from which we want modules,
        # as well as the archives from those
        for build_id in self._module_build:
            koji_queue.put(GetBuildCommand(ident=build_id, list_archives=True))

        # We'll need to obtain all container image builds
        for build_id in self._container_build:
            koji_queue.put(GetBuildCommand(ident=build_id, list_archives=True))

        # We'll need to obtain all virtual machine image builds
        for build_id in self._vmi_build:
            koji_queue.put(GetBuildCommand(ident=build_id, list_archives=True))

        # Put some threads to work on the queue.
        fetch_exceptions = []
        fetch_threads = [
            Thread(
                name="koji-%s-fetch-%s" % (id(self), i),
                target=self._do_fetch,
                args=(koji_queue, fetch_exceptions),
            )
            for i in range(0, self._threads)
        ]

        # Wait for all fetches to finish
        for t in fetch_threads:
            t.start()

        # If we are asked to shut down early then also shut down those threads
        # as soon as we can.
        def fetch_shutdown():
            try:
                # Empty the queue
                while True:
                    koji_queue.get_nowait()
            except Empty:
                pass

            # Then ask the threads to join
            for t in fetch_threads:
                t.join()

        self._on_shutdown.append(fetch_shutdown)

        for t in fetch_threads:
            t.join(self._timeout)

        # Re-raise exceptions, if any.
        # If we got more than one, we're only propagating the first.
        if fetch_exceptions:
            raise fetch_exceptions[0]

        # The queue must be empty now
        assert koji_queue.empty()

        push_items_fs = (
            self._modulemd_futures()
            + self._rpm_futures()
            + self._container_futures()
            + self._vmi_futures()
        )

        completed_fs = as_completed_with_timeout_reset(
            push_items_fs, timeout=self._timeout
        )
        for f in completed_fs:
            # If an exception occurred, this is where it will be raised.
            for pushitem in f.result():
                yield pushitem


Source.register_backend("koji", KojiSource)
