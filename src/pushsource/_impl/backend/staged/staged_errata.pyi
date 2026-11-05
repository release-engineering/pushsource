from os import DirEntry

from pushsource import ErratumPushItem
from pushsource._impl.backend.staged.staged_base import StagedBaseMixin
from pushsource._impl.backend.staged.staged_utils import StagingMetadata, StagingLeafDir

class StagedErrataMixin(StagedBaseMixin):
    def __make_push_item(
        self, leafdir: StagingLeafDir, metadata: StagingMetadata, entry: DirEntry
    ) -> ErratumPushItem: ...
