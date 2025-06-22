from os import DirEntry

from pushsource import AmiPushItem
from pushsource._impl.backend.staged.staged_base import StagedBaseMixin
from pushsource._impl.backend.staged.staged_utils import StagingLeafDir, StagingMetadata

class StagedAmiMixin(StagedBaseMixin):
    def __push_item(
        self, leafdir: StagingLeafDir, metadata: StagingMetadata, entry: DirEntry
    ) -> AmiPushItem: ...
