import os
import threading
import logging
from concurrent import futures

import six
from six.moves.urllib import parse
from six.moves.xmlrpc_client import ServerProxy
from more_executors import Executors
from more_executors.futures import f_map, f_zip

from .. import compat_attr as attr
from ..source import Source
from ..model import ErratumPushItem
from ..helpers import list_argument

LOG = logging.getLogger("pushsource")


class ErrataSource(Source):
    """Uses an advisory from Errata Tool as the source of push items."""

    def __init__(
        self,
        url,
        errata,
        target="cdn",
        koji_source=None,
        threads=4,
        timeout=60 * 60 * 4,
    ):
        """Create a new source.

        Parameters:
            url (src)
                Base URL of Errata Tool, e.g. "http://errata.example.com",
                "https://errata.example.com:8123".

            errata (str, list[str])
                Advisory ID(s) to be used as push item source.
                If a single string is given, multiple IDs may be
                comma-separated.

            target (str)
                The target type used when querying Errata Tool.
                The target type may influence the content produced,
                depending on the Errata Tool settings.

                Valid values include at least: "cdn", "rhn", "ftp".

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
        self._executor = Executors.thread_pool(max_workers=threads).with_retry()
        # We set aside a separate thread pool for koji so that there are separate
        # queues for ET and koji calls, yet we avoid creating a new thread pool for
        # each koji source.
        self._koji_executor = Executors.thread_pool(max_workers=threads).with_retry()
        self._koji_source_url = koji_source
        self._koji_factory = Source.get_partial(
            self._koji_source_url, cache={}, executor=self._koji_executor
        )
        self._target = target
        self._timeout = timeout
        self._tls = threading.local()

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
        return os.path.join(base, parsed.path, "errata/errata_service")

    @property
    def _errata_service(self):
        # XML-RPC client connected to errata_service.
        # Each thread uses a separate client.
        if not hasattr(self._tls, "errata_service"):
            url = self._errata_service_url
            LOG.debug("Creating XML-RPC client for Errata Tool: %s", url)
            self._tls.errata_service = ServerProxy(url)
        return self._tls.errata_service

    @property
    def _advisory_ids(self):
        # TODO: other cases (comma-separated; plain string)
        return self._errata

    def _get_advisory_metadata(self, advisory_id):
        # TODO: use CDN API even for RHN?
        return self._errata_service.get_advisory_cdn_metadata(advisory_id)

    def _get_advisory_file_list(self, advisory_id):
        # TODO: look at the target hint
        return self._errata_service.get_advisory_cdn_file_list(advisory_id)

    def _push_items_from_raw(self, metadata_and_file_list):
        (metadata, file_list) = metadata_and_file_list

        erratum = self._erratum_push_item_from_metadata(metadata)
        files = self._push_items_from_files(erratum, file_list)

        # The erratum should go to all the same destinations as the files.
        erratum_dest = set(erratum.dest or [])
        for file in files:
            for dest in file.dest:
                erratum_dest.add(dest)

        erratum = attr.evolve(erratum, dest=list(erratum_dest))

        return [erratum] + files

    def _erratum_push_item_from_metadata(self, metadata):

        # Translate from a raw metadata dict as provided by ET
        # into an ErratumPushItem object.
        kwargs = {}

        # Fill in the base push item attributes first.
        kwargs["name"] = metadata["id"]
        kwargs["state"] = "PENDING"

        # Now the erratum-specific fields.
        # Many are accepted verbatim from ET; these are mandatory (i.e. we'll crash
        # if the field is missing from ET).
        for field in [
            "type",
            "release",
            "status",
            "pushcount",
            "reboot_suggested",
            "rights",
            "title",
            "description",
            "version",
            "updated",
            "issued",
            "severity",
            "summary",
            "solution",
        ]:
            kwargs[field] = metadata[field]

        # Workaround to avoid python keyword
        kwargs["from_"] = metadata["from"]

        # If the metadata has a cdn_repo field, this sets the destinations for the
        # push item; used for text-only errata.
        #
        # Note that dest may also be added to later based on the file list in
        # the advisory.
        if metadata.get("cdn_repo"):
            kwargs["dest"] = metadata["cdn_repo"]

        # If there are content type hints, copy those while dropping the
        # pulp-specific terminology
        pulp_user_metadata = metadata.get("pulp_user_metadata") or {}
        if pulp_user_metadata.get("content_types"):
            kwargs["content_types"] = pulp_user_metadata["content_types"]

        return ErratumPushItem(**kwargs)

    def _push_items_from_files(self, erratum, file_list):
        out = []

        for build_nvr, build_info in six.iteritems(file_list):
            out.extend(self._push_items_from_build(erratum, build_nvr, build_info))

        return out

    def _push_items_from_build(self, erratum, build_nvr, build_info):
        rpms = build_info.get("rpms") or {}
        signing_key = build_info.get("sig_key") or None
        sha256sums = (build_info.get("checksums") or {}).get("sha256") or {}
        md5sums = (build_info.get("checksums") or {}).get("md5") or {}

        # Get a koji source which will yield all desired push items from this build.
        koji_source = self._koji_factory(rpm=list(rpms.keys()), signing_key=signing_key)

        out = []

        for push_item in koji_source:
            # Sanity check that the lookup by RPM filename matched the build
            # NVR expected by ET
            if push_item.build != build_nvr:
                raise ValueError(
                    "Push item NVR is wrong; expected: %s, item: %s"
                    % (build_nvr, repr(push_item))
                )

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

    def __iter__(self):
        """Iterate over push items for the given errata.

        - Yields :ref:`~pushsource.ErratumPushItem` instances for erratum metadata
        - Yields :ref:`~pushsource.RpmPushItem` instances for RPMs

        Other content types are not yet supported (most notably, container images).
        """

        # Get file list of all advisories first.
        #
        # We get the file list first because it contains koji build NVRs,
        # so by getting these first we can issue koji build queries and advisory
        # metadata queries concurrently.
        file_list_fs = [
            self._executor.submit(self._get_advisory_file_list, advisory_id)
            for advisory_id in self._advisory_ids
        ]

        # Then get metadata.
        metadata_fs = [
            self._executor.submit(self._get_advisory_metadata, advisory_id)
            for advisory_id in self._advisory_ids
        ]

        # Zip up the metadata and file list for each advisory, since both are
        # needed together in order to make push items.
        advisory_fs = [
            f_zip(metadata_f, file_list_f)
            for (metadata_f, file_list_f) in zip(metadata_fs, file_list_fs)
        ]

        # Convert them to lists of push items
        advisory_push_items_fs = [
            f_map(f, self._push_items_from_raw) for f in advisory_fs
        ]

        completed_fs = futures.as_completed(
            advisory_push_items_fs, timeout=self._timeout
        )
        for f in completed_fs:
            # If an exception occurred, this is where it will be raised.
            for pushitem in f.result():
                yield pushitem


Source.register_backend("errata", ErrataSource)
