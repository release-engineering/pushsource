import logging
import os

try:
    from os import scandir
except ImportError:
    # TODO: is scandir able to work on python 2.6?
    from scandir import scandir

from ...model import FilePushItem

LOG = logging.getLogger("pushsource")


class StagedFilesMixin(object):
    _FILE_TYPES = {}

    def __init__(self, *args, **kwargs):
        super(StagedFilesMixin, self).__init__(*args, **kwargs)
        self._FILE_TYPES = self._FILE_TYPES.copy()
        self._FILE_TYPES["ISOS"] = self.__file_push_items
        self._FILE_TYPES["FILES"] = self._FILE_TYPES["ISOS"]

    def __file_push_items(self, leafdir, metadata):
        out = []

        LOG.debug("Looking for files in %s", leafdir)

        for entry in scandir(leafdir.path):
            if entry.is_file():
                out.append(self.__make_push_item(leafdir, metadata, entry))

        return out

    def __make_push_item(self, leafdir, metadata, entry):
        relative_path = os.path.join(leafdir.dest, leafdir.file_type, entry.name)
        file_md = metadata.file_metadata.get(relative_path)

        if not file_md:
            msg = "%s doesn't contain data for %s" % (metadata.filename, relative_path)
            LOG.error(msg)
            raise ValueError(msg)

        return FilePushItem(
            name=file_md.filename or entry.name,
            src=entry.path,
            description=file_md.attributes.get("description"),
            sha256sum=file_md.sha256sum,
            # TODO: decide if this is correct field for origin.
            origin="staged",
            dest=[leafdir.dest],
        )
