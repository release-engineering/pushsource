import os
import threading
import logging
import itertools
import functools

from concurrent import futures

import yaml
import json

try:
    from os import scandir
except ImportError:
    # TODO: is scandir able to work on python 2.6?
    from scandir import scandir

from pushcollector import Collector
from more_executors import Executors

from ...source import Source
from .staged_utils import StagingMetadata, StagingLeafDir

# from ..model import RpmPushItem
from ...helpers import list_argument

from .staged_files import StagedFilesMixin

LOG = logging.getLogger("pushsource")
METADATA_FILES = ["staged.yaml", "staged.yml", "staged.json", "pub-mapfile.json"]
CACHE_LOCK = threading.RLock()


class StagedSource(Source, StagedFilesMixin):
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
        self._executor = (
            Executors.thread_pool(max_workers=threads)
            .with_timeout(timeout)
            .with_retry()
        )

    #         FILE_TYPE_PATHS = {
    #     'rpm': ['RPMS', 'SRPMS'],
    #     'comps': ['COMPS'],
    #     'iso': ['ISOS', 'FILES'],
    #     'docker': ['DOCKER'],
    #     'productid': ['PRODUCTID'],
    #     'modulemd': ['MODULEMD'],
    #     'erratum': ['ERRATA'],
    #     'channel_dump': ['CHANNEL_DUMPS'],
    #     'aws_image': ['AWS_IMAGES'],
    # }

    def __iter__(self):
        """Iterate over push items."""

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
        return self._FILE_TYPES[leafdir.file_type](leafdir=leafdir, metadata=metadata)

    def _push_items_for_topdir(self, topdir):
        LOG.debug("Checking files in: %s", topdir)

        destdirs = []
        for entry in scandir(topdir):
            if entry.is_dir() and entry.name != "logs":
                destdirs.append(entry.path)

        if not destdirs:
            LOG.warning("%s has no destination directories", topdir)
            return

        metadata = self._load_metadata(topdir)

        # All directories which may contain files to be processed
        all_leaf_dirs = []
        for destdir in destdirs:
            for file_type in self._FILE_TYPES:
                path = os.path.join(destdir, file_type)
                LOG.debug("Scanning %s", path)
                if os.path.exists(path):
                    # OK, this is a directory we'll have to look into.
                    all_leaf_dirs.append(
                        StagingLeafDir(
                            dest=os.path.basename(destdir),
                            file_type=file_type,
                            path=path,
                        )
                    )

        process_dir = functools.partial(self._push_items_for_leafdir, metadata=metadata)
        pushitems_fs = [
            self._executor.submit(process_dir, leafdir) for leafdir in all_leaf_dirs
        ]

        completed_fs = futures.as_completed(pushitems_fs, timeout=self._timeout)
        for f in completed_fs:
            for pushitem in f.result():
                yield pushitem

        #     file_channel_mapping = {}

        #     def get_file_channel_mapping(sself, data, num, lock):
        #         channel, file_type = data
        #         for d in FILE_TYPE_PATHS[file_type]:
        #             channel_staging_dir = os.path.abspath(
        #                 os.path.join(staging_dir, channel, d)
        #             )
        #             if not os.path.isdir(channel_staging_dir):
        #                 continue
        #             for fn in os.listdir(channel_staging_dir):
        #                 file_path = os.path.join(channel_staging_dir, fn)
        #                 if not os.path.isfile(file_path):
        #                     continue
        #                 # has to be removed in future - now staging scripts
        #                 # incorrectly put productid to RPMS directory
        #                 if file_type == "rpm" and fn == "productid":
        #                     continue
        #                 lock.acquire()
        #                 try:
        #                     file_channel_mapping.setdefault(
        #                         file_path, {"channels": set(), "file_type": file_type}
        #                     )
        #                     file_channel_mapping[file_path]["channels"].add(channel)
        #                     if file_type in (
        #                         "iso",
        #                         "docker",
        #                         "channel_dump",
        #                         "aws_image",
        #                     ):
        #                         if not md:
        #                             raise IOError
        #                         if file_path not in md:
        #                             msg = (
        #                                 "pub-mapfile.json doesn't contain data for %s"
        #                                 % file_path
        #                             )
        #                             self.push.log_error(msg)
        #                             raise ValueError(msg)
        #                         file_channel_mapping[file_path]["md"] = md[file_path]
        #                 finally:
        #                     lock.release()

        #     dirs = []
        #     for channel in channel_dirs:
        #         for file_type in six.iterkeys(FILE_TYPE_PATHS):
        #             dirs.append((channel, file_type))
        #     try:
        #         run_in_threads(get_file_channel_mapping, dirs, threads=5, use_lock=True)
        #     except IOError:
        #         msg = "No pub-mapfile.json found in directory %s" % staging_dir
        #         self.push.log_error(msg)
        #         self.push.fail_push()

        #     if not file_channel_mapping:
        #         self.push.log_warning("{0} has no channel files".format(staging_dir))
        #         continue

        #     if self.push.target_info["target_type"]["name"] == "altsrc":
        #         self.populate_altsrc_push_items(file_channel_mapping, staging_dir)
        #         return
        #     re_comps = re.compile(r".*comps.*xml$")
        #     for file_path, data in six.iteritems(file_channel_mapping):
        #         channels = list(data["channels"])
        #         item = self._get_blank_push_item()
        #         item.origin = staging_dir
        #         item.file_name = os.path.basename(file_path)
        #         item.file_path = file_path
        #         item.add_repo(channels)
        #         if data["file_type"] == "iso":
        #             item.file_type = "iso"
        #             item.file_name = data["md"]["filename"]
        #             item.metadata["description"] = data["md"]["attributes"][
        #                 "description"
        #             ]
        #             item.metadata["version"] = data["md"]["version"]
        #         elif re_comps.match(item.file_name):
        #             item.file_type = "comps"
        #         elif data["file_type"] == "docker":
        #             item.file_type = "docker"
        #             tags = data.get("md", {}).get("attributes", {}).get("tags", [])
        #             if not is_docker_archive(item.file_path):
        #                 self.push.log_warning(
        #                     "%s seems to be invalid docker archive" % item.file_path
        #                 )
        #             for channel in channels:
        #                 item.set_tags_for_repo(channel, tags)
        #         elif data["file_type"] == "channel_dump":
        #             item.file_type = "channel_dump"
        #             for attr in CHANNEL_DUMP_FIELDS:
        #                 if attr not in data["md"]["attributes"]:
        #                     msg = "File %s doesn't contain attribute %s" % (
        #                         item.file_name,
        #                         attr,
        #                     )
        #                     self.push.log_error(msg)
        #                     raise ValueError(msg)
        #                 item.metadata[attr] = data["md"]["attributes"][attr]
        #         elif data["file_type"] == "productid":
        #             item.file_type = "productid"
        #         elif data["file_type"] == "modulemd":
        #             item.file_type = "modulemd"
        #         elif data["file_type"] == "erratum":
        #             item.file_type = "erratum"
        #         elif data["file_type"] == "aws_image":
        #             item.file_type = "aws_image"
        #             attrs = data["md"]["attributes"]
        #             cloudupload.validate_metadata(attrs)

        #             for channel in channels:
        #                 # Make sure the destination/channel name is the same as
        #                 # a combination of the region and image type from the
        #                 # item's attributes
        #                 if channel != attrs["region"] + "-" + attrs["type"]:
        #                     msg = (
        #                         "Region and/or image type metadata does "
        #                         + "not match destination for %s" % file_path
        #                     )
        #                     self.push.log_error(msg)
        #                     raise ValueError(msg)

        #                 # Store the attributes under a key with the channel
        #                 # name. This will allow us to preserve channel specific
        #                 # metadata should this item's metadata be combined with
        #                 # another item's metadata.
        #                 item.metadata[channel] = attrs

        #         elif item.file_name.endswith(".rpm"):
        #             item.file_type = "rpm"
        #         else:
        #             self.push.log_error("Unknown file type: %s" % file_path)
        #             e = UnknownFileType(file_path)
        #             item.add_error(PUSH_ITEM_STATES["INVALIDFILE"], e)
        #             raise e

        #         self._adjust_push_item(item)
        #         self.add_item(item)
        #         added += 1
        #         if added % 1 == 5000:
        #             self.push.log_debug("Statted %s files" % added)


Source.register_backend("staged", StagedSource)
