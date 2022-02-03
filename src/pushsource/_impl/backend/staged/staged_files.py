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
        file_md = metadata.file_metadata_or_die(relative_path)

        return FilePushItem(
            name=file_md.filename or entry.name,
            src=entry.path,
            description=file_md.attributes.get("description"),
            version=file_md.version,
            display_order=file_md.order,
            sha256sum=file_md.sha256sum,
            origin=leafdir.topdir,
            dest=[leafdir.dest],
        )
