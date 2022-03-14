import os
import threading
import logging
import itertools
import functools

import yaml
import json

from pushsource._impl.compat import scandir

from pushcollector import Collector
from more_executors import Executors

from ...source import Source
from ...model import DirectoryPushItem
from ...helpers import list_argument, as_completed_with_timeout_reset

from .staged_utils import StagingMetadata, StagingLeafDir
from .staged_ami import StagedAmiMixin
from .staged_files import StagedFilesMixin
from .staged_errata import StagedErrataMixin
from .staged_compsxml import StagedCompsXmlMixin
from .staged_modulemd import StagedModuleMdMixin
from .staged_productid import StagedProductIdMixin
from .staged_rpm import StagedRpmMixin
from .staged_unsupported import StagedUnsupportedMixin

LOG = logging.getLogger("pushsource")
METADATA_FILES = ["staged.yaml", "staged.yml", "staged.json", "pub-mapfile.json"]
CACHE_LOCK = threading.RLock()


class StagedSource(
    Source,
    StagedAmiMixin,
    StagedFilesMixin,
    StagedErrataMixin,
    StagedCompsXmlMixin,
    StagedModuleMdMixin,
    StagedProductIdMixin,
    StagedRpmMixin,
    StagedUnsupportedMixin,
):
    """Uses a directory with a predefined layout (a "staging directory") as
    the source of push items."""

    # To keep code maintainable, this class doesn't directly support any file
    # types; separate files are expected to register themselves here.
    _FILE_TYPES = {}

    def __init__(self, url, threads=4, timeout=60 * 60):
        """Create a new source.

        Parameters:
            url (list[str])
                URL(s) of locally accessible staging directories, e.g.
                ``"/mnt/staging/my-content-for-push"``.

                These directories must follow the documented layout for staging areas.

            threads (int)
                Number of threads used for concurrent loading of files.

            timeout (int)
                Number of seconds after which an error is raised, if no progress is
                made during each step.

        """
        super(StagedSource, self).__init__()
        self._url = list_argument(url)
        self._threads = threads
        self._timeout = timeout

        # Note: this executor does not have a retry.
        # NFS already does a lot of its own retries.
        self._executor = (
            Executors.thread_pool(name="pushsource-staged", max_workers=threads)
            .with_timeout(timeout)
            .with_cancel_on_shutdown()
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._executor.shutdown()

    def __iter__(self):
        # Possible improvement would be to handle the separate dirs concurrently.
        # However, may not be worthwhile, as  in practice I'm not sure the ability
        # to pass more than a single staging directory is ever used (?)
        return itertools.chain(
            *[self._push_items_for_topdir(x) for x in self._url]
        ).__iter__()

    def _load_metadata(self, topdir):
        # Load the top-level metadata file in the staging directory, if any.
        for candidate in METADATA_FILES:
            metadata_file = os.path.join(topdir, candidate)
            if os.path.exists(metadata_file):
                break
        else:
            # no metadata file
            return StagingMetadata()

        basename = os.path.basename(metadata_file)

        with open(metadata_file, "rt") as f:
            content = f.read()

            # Save a copy of the file for later reference
            Collector.get().attach_file(basename, content).result()

            if metadata_file.endswith(".json"):
                metadata = json.loads(content)
            else:
                metadata = yaml.safe_load(content)

        return StagingMetadata.from_data(metadata, os.path.basename(metadata_file))

    def _push_items_for_leafdir(self, leafdir, metadata):
        LOG.debug("Scanning %s", leafdir.path)
        if not os.path.exists(leafdir.path):
            return []
        if leafdir.file_type == "RAW":
            return [
                DirectoryPushItem(
                    name=leafdir.dest, src=leafdir.path, dest=[leafdir.dest]
                )
            ]
        return self._FILE_TYPES[leafdir.file_type](leafdir=leafdir, metadata=metadata)

    def _push_items_for_topdir(self, topdir):
        LOG.info("Checking files in: %s", topdir)

        metadata = self._load_metadata(topdir)

        destdirs = []
        for entry in scandir(topdir):
            if entry.is_dir() and entry.name != "logs":
                destdirs.append(entry.path)

        if not destdirs:
            LOG.warning("%s has no destination directories", topdir)
            # If there's no directories AND no metadata file, the caller most likely
            # provided an incorrect path. (If the caller expects to provide empty
            # staging areas sometimes, they can signal this by including empty metadata.)
            if not metadata.filename:
                raise IOError("%s does not appear to be a staging directory" % topdir)
            return

        # All directories which may contain files to be processed
        all_leaf_dirs = []
        for destdir in destdirs:
            for file_type in ["RAW"] + list(self._FILE_TYPES):
                path = os.path.join(destdir, file_type)
                all_leaf_dirs.append(
                    StagingLeafDir(
                        dest=os.path.basename(destdir),
                        file_type=file_type,
                        path=path,
                        topdir=topdir,
                    )
                )

        process_dir = functools.partial(self._push_items_for_leafdir, metadata=metadata)
        pushitems_fs = [
            self._executor.submit(process_dir, leafdir) for leafdir in all_leaf_dirs
        ]

        completed_fs = as_completed_with_timeout_reset(
            pushitems_fs, timeout=self._timeout
        )
        for f in completed_fs:
            for pushitem in f.result():
                yield pushitem


Source.register_backend("staged", StagedSource)
