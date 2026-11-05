from os import DirEntry

from .staged_utils import StagingLeafDir, StagingMetadata
from ...model import ProductIdPushItem
from .staged_base import StagedBaseMixin

class StagedProductIdMixin(StagedBaseMixin):
    def __push_item(
        self, leafdir: StagingLeafDir, _: StagingMetadata, entry: DirEntry
    ) -> ProductIdPushItem: ...
