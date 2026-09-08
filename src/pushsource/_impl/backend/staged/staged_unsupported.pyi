from os import DirEntry

from .staged_base import StagedBaseMixin
from .staged_utils import StagingLeafDir, StagingMetadata

class StagedUnsupportedMixin(StagedBaseMixin):
    def __push_item(
        self, _leafdir: StagingLeafDir, _metadata: StagingMetadata, entry: DirEntry
    ) -> None: ...
