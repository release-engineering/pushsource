import os
import logging
from concurrent import futures

import six
from six.moves.urllib import parse
from more_executors import Executors

from .errata_client import ErrataClient

from ... import compat_attr as attr
from ...source import Source
from ...model import ErratumPushItem
from ...helpers import list_argument

LOG = logging.getLogger("pushsource")


class ErrataSource(Source):
    """Uses an advisory from Errata Tool as the source of push items."""

    def __init__(self, url, errata, koji_source=None, threads=4, timeout=60 * 60 * 4):
        """Create a new source.

        Parameters:
            url (src)
                Base URL of Errata Tool, e.g. "http://errata.example.com",
                "https://errata.example.com:8123".

            errata (str, list[str])
                Advisory ID(s) to be used as push item source.
                If a single string is given, multiple IDs may be
                comma-separated.

            koji_source (str)
                URL of a koji source associated with this Errata Tool
                instance.

            threads (int)
                Number of threads used for concurrent queries to Errata Tool
                and koji.

            timeout (int)
                Number of seconds after which an error is raised, if no progress is
                made during queries to Errata Tool.
        """
        self._url = url
        self._errata = list_argument(errata)
        self._client = ErrataClient(threads=threads, url=self._errata_service_url)

        # This executor doesn't use retry because koji & ET executors already do that.
        self._executor = Executors.thread_pool(max_workers=threads)

        # We set aside a separate thread pool for koji so that there are separate
        # queues for ET and koji calls, yet we avoid creating a new thread pool for
        # each koji source.
        self._koji_executor = Executors.thread_pool(max_workers=threads).with_retry()
        self._koji_cache = {}
        self._koji_source_url = koji_source
        self._timeout = timeout

    @property
    def _errata_service_url(self):
        # URL for the errata_service XML-RPC endpoint provided by ET.
        #
        # Note the odd handling of scheme here. The reason is that
        # ET oddly provides different APIs over http and https.
        #
        # This XML-RPC API is available anonymously over *http* only,
        # but since this might change in the future, the caller is
        # allowed to provide http or https scheme and we'll apply the
        # scheme we know is actually needed.
        parsed = parse.urlparse(self._url)
        base = "http://" + parsed.netloc
        return os.path.join(base + parsed.path, "errata/errata_service")

    def _koji_source(self, **kwargs):
        if not self._koji_source_url:
            raise ValueError("A Koji source is required but none is specified")
        return Source.get(
            self._koji_source_url,
            cache=self._koji_cache,
            executor=self._koji_executor,
            **kwargs
        )

    @property
    def _advisory_ids(self):
        # TODO: other cases (comma-separated; plain string)
        return self._errata

    def _push_items_from_raw(self, raw):
        erratum = ErratumPushItem._from_data(raw.advisory_cdn_metadata)

        rpms = self._push_items_from_rpms(erratum, raw.advisory_cdn_file_list)

        # The erratum should go to all the same destinations as the rpms,
        # before FTP paths are added.
        erratum_dest = set(erratum.dest or [])
        for rpm in rpms:
            for dest in rpm.dest:
                erratum_dest.add(dest)
        erratum = attr.evolve(erratum, dest=sorted(erratum_dest))

        # Enrich RPM push items with their FTP paths if any.
        rpms = self._add_ftp_paths(rpms, raw.ftp_paths)

        return [erratum] + rpms

    def _push_items_from_rpms(self, erratum, rpm_list):
        out = []

        for build_nvr, build_info in six.iteritems(rpm_list):
            out.extend(self._rpm_push_items_from_build(erratum, build_info))
            out.extend(
                self._module_push_items_from_build(erratum, build_nvr, build_info)
            )

        return out

    def _module_push_items_from_build(self, erratum, build_nvr, build_info):
        modules = (build_info.get("modules") or {}).copy()

        # Get a koji source which will yield all modules from the build
        koji_source = self._koji_source(
            module_build=[build_nvr], module_filter_filename=list(modules.keys())
        )

        out = []

        for push_item in koji_source:
            # ET uses filenames to identify the modules here, we must do the same.
            basename = os.path.basename(push_item.src)
            dest = modules.pop(basename)

            # Fill in more push item details based on the info provided by ET.
            push_item = attr.evolve(push_item, dest=dest, origin=erratum.name)

            out.append(push_item)

        # Were there any requested modules we couldn't find?
        missing_modules = ", ".join(sorted(modules.keys()))
        if missing_modules:
            msg = "koji build {nvr} does not contain {missing} (requested by advisory {erratum})".format(
                nvr=build_nvr, missing=missing_modules, erratum=erratum.name
            )
            raise ValueError(msg)

        return out

    def _rpm_push_items_from_build(self, erratum, build_info):
        rpms = build_info.get("rpms") or {}
        signing_key = build_info.get("sig_key") or None
        sha256sums = (build_info.get("checksums") or {}).get("sha256") or {}
        md5sums = (build_info.get("checksums") or {}).get("md5") or {}

        # Get a koji source which will yield all desired push items from this build.
        koji_source = self._koji_source(rpm=list(rpms.keys()), signing_key=signing_key)

        out = []

        for push_item in koji_source:
            # Do not allow to proceed if RPM was absent
            if push_item.state == "NOTFOUND":
                raise ValueError(
                    "Advisory refers to %s but RPM was not found in koji"
                    % push_item.name
                )

            # Note, we can't sanity check here that the push item's build
            # equals ET's NVR, because it's not always the case.
            # Example:
            #  RPM: pgaudit-debuginfo-1.4.0-4.module+el8.1.1+4794+c82b6e09.x86_64.rpm
            #  belongs to build: 1015162 (pgaudit-1.4.0-4.module+el8.1.1+4794+c82b6e09)
            #  but ET refers instead to module build: postgresql-12-8010120191120141335.e4e244f9.

            # Fill in more push item details based on the info provided by ET.
            push_item = attr.evolve(
                push_item,
                sha256sum=sha256sums.get(push_item.name),
                md5sum=md5sums.get(push_item.name),
                dest=rpms.get(push_item.name),
                origin=erratum.name,
            )

            out.append(push_item)

        return out

    def _add_ftp_paths(self, rpm_items, ftp_paths):
        # ftp_paths structure is like this:
        #
        # {
        #     "xorg-x11-server-1.20.4-16.el7_9": {
        #         "rpms": {
        #             "xorg-x11-server-1.20.4-16.el7_9.src.rpm": [
        #                 "/ftp/pub/redhat/linux/enterprise/7Client/en/os/SRPMS/",
        #                 "/ftp/pub/redhat/linux/enterprise/7ComputeNode/en/os/SRPMS/",
        #                 "/ftp/pub/redhat/linux/enterprise/7Server/en/os/SRPMS/",
        #                 "/ftp/pub/redhat/linux/enterprise/7Workstation/en/os/SRPMS/",
        #             ]
        #         },
        #         "sig_key": "fd431d51",
        #     }
        # }
        #
        # We only care about the rpm => ftp path mapping, which should be added onto
        # our existing rpm push items if any exist.
        #
        rpm_to_paths = {}
        for rpm_map in ftp_paths.values():
            for (rpm_name, paths) in (rpm_map.get("rpms") or {}).items():
                rpm_to_paths[rpm_name] = paths

        out = []
        for item in rpm_items:
            paths = rpm_to_paths.get(item.name) or []
            item = attr.evolve(item, dest=item.dest + paths)
            out.append(item)

        return out

    def __iter__(self):
        # Get raw ET responses for all errata.
        raw_fs = [self._client.get_raw_f(id) for id in self._advisory_ids]

        # Convert them to lists of push items
        push_items_fs = []
        for f in futures.as_completed(raw_fs, timeout=self._timeout):
            push_items_fs.append(
                self._executor.submit(self._push_items_from_raw, f.result())
            )

        completed_fs = futures.as_completed(push_items_fs, timeout=self._timeout)
        for f in completed_fs:
            for pushitem in f.result():
                yield pushitem


Source._register_backend_builtin("errata", ErrataSource)
