from os import DirEntry

from pushsource import CompsXmlPushItem
from pushsource._impl.backend.staged.staged_base import StagedBaseMixin
from pushsource._impl.backend.staged.staged_utils import StagingLeafDir, StagingMetadata

class StagedCompsXmlMixin(StagedBaseMixin):
    def __push_item(
        self, leafdir: StagingLeafDir, _: StagingMetadata, entry: DirEntry
    ) -> CompsXmlPushItem: ...
