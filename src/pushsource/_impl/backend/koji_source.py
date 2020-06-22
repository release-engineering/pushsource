import os
import threading
import logging
from functools import partial

from concurrent import futures
from six.moves.queue import Queue, Empty
from threading import Thread

import koji
from more_executors import Executors
from more_executors.futures import f_map

from ..source import Source
from ..model import RpmPushItem, ModuleMdPushItem
from ..helpers import list_argument, try_int

LOG = logging.getLogger("pushsource")
CACHE_LOCK = threading.RLock()


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
                The source will yield all modulemd files belonging to these
                build(s).

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
        self._signing_key = list_argument(signing_key)
        self._dest = list_argument(dest)
        self._timeout = timeout
        self._pathinfo = koji.PathInfo(basedir)
        self._cache = {} if cache is None else cache
        self._threads = threads
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

        # If signing keys requested, try them in order of preference
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

    def _push_items_from_module_build(self, nvr, meta):
        LOG.debug("Looking for modulemd on %s, %s", nvr, meta)

        if not meta:
            message = "Module build not found in koji: %s" % nvr
            LOG.error(message)
            raise ValueError(message)

        build_id = meta["id"]
        archives = self._get_archives(build_id)
        modules = [elem for elem in archives if elem.get("btype") == "module"]

        out = []
        for module in modules:
            file_path = os.path.join(
                self._pathinfo.typedir(meta, "module"), module["filename"]
            )
            # Possible TODO: koji also provides a checksum, which could be filled
            # in here. However, it seems to be only MD5?
            out.append(
                ModuleMdPushItem(
                    name=module["filename"],
                    src=file_path,
                    dest=self._dest,
                    build=meta["nvr"],
                )
            )
        return out

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
        for t in fetch_threads:
            t.join(self._timeout)

        # Re-raise exceptions, if any.
        # If we got more than one, we're only propagating the first.
        if fetch_exceptions:
            raise fetch_exceptions[0]

        # The queue must be empty now
        assert koji_queue.empty()

        push_items_fs = self._modulemd_futures() + self._rpm_futures()

        completed_fs = futures.as_completed(push_items_fs, timeout=self._timeout)
        for f in completed_fs:
            # If an exception occurred, this is where it will be raised.
            for pushitem in f.result():
                yield pushitem


Source.register_backend("koji", KojiSource)
