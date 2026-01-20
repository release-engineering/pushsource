from os import DirEntry

from pushsource import FilePushItem
from pushsource._impl.backend.staged.staged_base import StagedBaseMixin
from pushsource._impl.backend.staged.staged_utils import StagingLeafDir, StagingMetadata

class StagedFilesMixin(StagedBaseMixin):
    def __file_push_item(
        self, leafdir: StagingLeafDir, metadata: StagingMetadata, entry: DirEntry
    ) -> FilePushItem: ...
