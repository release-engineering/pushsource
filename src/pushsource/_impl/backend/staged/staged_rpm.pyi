from os import DirEntry

from .staged_base import StagedBaseMixin
from .staged_utils import StagingLeafDir, StagingMetadata
from ...model import RpmPushItem

class StagedRpmMixin(StagedBaseMixin):
    def __push_item(
        self, leafdir: StagingLeafDir, _: StagingMetadata, entry: DirEntry
    ) -> RpmPushItem: ...
