import logging
from ...model import CGWPushItem
from .staged_base import StagedBaseMixin, handles_type

LOG = logging.getLogger("pushsource")


class StagedCGWMixin(StagedBaseMixin):
    @handles_type("CGW")
    def __push_item(self, leafdir, _, entry):
        return CGWPushItem(
            name=entry.name, src=entry.path, origin=leafdir.topdir, dest=[leafdir.dest]
        )
