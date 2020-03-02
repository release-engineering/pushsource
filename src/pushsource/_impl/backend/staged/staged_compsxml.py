from ...model import CompsXmlPushItem
from .staged_base import StagedBaseMixin, handles_type


class StagedCompsXmlMixin(StagedBaseMixin):
    @handles_type("COMPS")
    def __push_item(self, leafdir, _, entry):
        return CompsXmlPushItem(
            name=entry.name, src=entry.path, origin=leafdir.topdir, dest=[leafdir.dest]
        )
