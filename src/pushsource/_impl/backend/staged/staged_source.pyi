from collections import Sequence, Mapping, Iterator, MutableMapping, Generator
from threading import RLock as ReentrantLock
from types import TracebackType
from typing import Final, ClassVar, Type

from .staged_base import PartialTypeHandler
from .staged_utils import StagingMetadata, StagingLeafDir
from ...model.base import PushItem_co, PushItem
from ...source import Source

from .staged_ami import StagedAmiMixin
from .staged_compsxml import StagedCompsXmlMixin
from .staged_errata import StagedErrataMixin
from .staged_files import StagedFilesMixin
from .staged_modulemd import StagedModuleMdMixin
from .staged_productid import StagedProductIdMixin
from .staged_rpm import StagedRpmMixin
from .staged_unsupported import StagedUnsupportedMixin

METADATA_FILES: Final[Sequence[str]]
CACHE_LOCK: Final[ReentrantLock]

class StagedSource(
    Source,
    StagedAmiMixin,
    StagedFilesMixin,
    StagedErrataMixin,
    StagedCompsXmlMixin,
    StagedModuleMdMixin,
    StagedProductIdMixin,
    StagedRpmMixin,
    StagedUnsupportedMixin,
):
    _FILE_TYPES = Final[ClassVar[MutableMapping[str, PartialTypeHandler]]]
    def __init__(
        self, url: Sequence[str], threads: int = ..., timeout: int = ...
    ) -> None: ...
    def __enter__(self) -> "Source": ...
    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ): ...
    def __iter__(self) -> Iterator[PushItem_co]: ...
    def _load_metadata(self, topdir: str) -> StagingMetadata: ...
    def _push_items_for_leafdir(
        self, leafdir: StagingLeafDir, metadata: StagingMetadata
    ) -> Sequence[PushItem_co]: ...
    def _push_items_for_topdir(self, topdir: str) -> Iterator[PushItem_co]: ...
