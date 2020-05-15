from ...model import ProductIdPushItem
from .staged_base import StagedBaseMixin, handles_type


class StagedProductIdMixin(StagedBaseMixin):
    @handles_type("PRODUCTID")
    def __push_item(self, leafdir, _, entry):
        return ProductIdPushItem(
            name=entry.name, src=entry.path, origin=leafdir.topdir, dest=[leafdir.dest]
        )
