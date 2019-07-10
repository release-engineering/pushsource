import os
import threading
import logging
from functools import partial

from concurrent import futures

import koji
from more_executors import Executors
from more_executors.futures import f_map

from ..source import Source
from ..model import RpmPushItem
from ..helpers import list_argument

LOG = logging.getLogger("pushsource")
CACHE_LOCK = threading.RLock()


class KojiSource(Source):
    """Uses koji artifacts as the source of push items."""

    def __init__(
        self,
        url,
        dest=None,
        rpm=None,
        signing_key=None,
        basedir=None,
        threads=4,
        timeout=60 * 2,
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

                If provided, `threads` has no effect.
        """
        self._url = url
        self._rpm = list_argument(rpm)
        self._signing_key = list_argument(signing_key)
        self._dest = list_argument(dest)
        self._timeout = timeout
        self._pathinfo = koji.PathInfo(basedir)
        self._cache = {} if cache is None else cache
        self._executor = (
            executor or Executors.thread_pool(max_workers=threads).with_retry()
        )

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

    def _get_rpm(self, rpm):
        with CACHE_LOCK:
            if rpm not in self._cache.setdefault("rpm", {}):
                LOG.debug("Get koji RPM %s", rpm)
                self._cache["rpm"][rpm] = self._koji_session.getRPM(rpm)

        return self._cache["rpm"][rpm]

    def _get_build(self, build_id):
        with CACHE_LOCK:
            if build_id not in self._cache.setdefault("build", {}):
                LOG.debug("Get koji build %s", build_id)
                self._cache["build"][build_id] = self._koji_session.getBuild(build_id)

        return self._cache["build"][build_id]

    def _push_items_from_rpm_meta(self, rpm, meta):
        LOG.debug("RPM metadata for %s: %s", rpm, meta)

        notfound = [RpmPushItem(name=rpm, dest=self._dest, state="NOTFOUND")]

        if not meta:
            LOG.error("RPM not found in koji: %s", rpm)
            return notfound

        build = self._get_build(meta["build_id"])
        build_path = self._pathinfo.build(build)
        rpm_path = None
        unsigned_path = os.path.join(build_path, self._pathinfo.rpm(meta))
        rpm_signing_key = None

        # If signing keys requested, try them in order of preference
        for key in self._signing_key:
            if key:
                key = key.lower()
                candidate = os.path.join(build_path, self._pathinfo.signed(meta, key))
            else:
                candidate = unsigned_path
            if os.path.exists(candidate):
                rpm_path = candidate
                rpm_signing_key = key
                break

        if self._signing_key:
            # If signing keys requested: we either found an RPM above, or an error occurs
            if not rpm_path:
                LOG.error(
                    "RPM not found in koji with signing key(s) %s: %s",
                    ", ".join(self._signing_key),
                    rpm,
                )
                return notfound
        else:
            # If no signing key requested, we just use the calculated path directly
            # and don't even test for its existence. Note: absence of test for existence
            # is ported from old code and is not necessarily the best way.
            rpm_path = unsigned_path

        # TODO: RpmPushItem?

        return [
            RpmPushItem(
                name=os.path.basename(rpm_path),
                src=rpm_path,
                dest=self._dest,
                signing_key=rpm_signing_key,
                build=build["nvr"],
            )
        ]

    def __iter__(self):
        """Iterate over push items.

        - Yields :ref:`~pushsource.RpmPushItem` instances for RPMs
        """

        # Get info from each requested RPM.
        rpm_fs = [(self._executor.submit(self._get_rpm, rpm), rpm) for rpm in self._rpm]

        # Convert them to lists of push items
        rpm_push_items_fs = [
            f_map(f, partial(self._push_items_from_rpm_meta, rpm=rpm))
            for f, rpm in rpm_fs
        ]

        completed_fs = futures.as_completed(rpm_push_items_fs, timeout=self._timeout)
        for f in completed_fs:
            # If an exception occurred, this is where it will be raised.
            for pushitem in f.result():
                yield pushitem


Source.register_backend("koji", KojiSource)
