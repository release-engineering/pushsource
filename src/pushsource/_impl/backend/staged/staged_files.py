import logging
import os

from ...model import FilePushItem
from .staged_base import StagedBaseMixin, handles_type

LOG = logging.getLogger("pushsource")


class StagedFilesMixin(StagedBaseMixin):
    @handles_type("ISOS")
    @handles_type("FILES")
    def __file_push_item(self, leafdir, metadata, entry):
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
