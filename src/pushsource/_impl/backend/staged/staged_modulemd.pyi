from os import DirEntry

from pushsource import ModuleMdPushItem
from pushsource._impl.backend.staged.staged_base import StagedBaseMixin
from pushsource._impl.backend.staged.staged_utils import StagingLeafDir, StagingMetadata

class StagedModuleMdMixin(StagedBaseMixin):
    def __push_item(
        self, leafdir: StagingLeafDir, metadata: StagingMetadata, entry: DirEntry
    ) -> ModuleMdPushItem: ...
