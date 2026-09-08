from collections import Callable, Sequence
from os import DirEntry
from typing import Final, ClassVar, MutableMapping, Any

from pushsource import PushItem
from pushsource._impl.backend.staged.staged_utils import StagingLeafDir, StagingMetadata
from pushsource._impl.model.base import PushItem_co

# Typically "self" isn't annotated, but in this case
# "unbound" methods are being stashed in a dict and
# the "self" parameter is not fulfilled until later via
# partial application. This type annotation accounts for
# the type of unbound "self" parameter in the callable signature.
UnboundTypeHandlerDelegate = Callable[
    ["StagedBaseMixin", StagingLeafDir, StagingMetadata, DirEntry], PushItem
]
# A type for an UnboundTypeHandlerDelegate where "self" has
# been bound to an instance of StagedBaseMixin
BoundTypeHandlerDelegate = Callable[
    [StagingLeafDir, StagingMetadata, DirEntry], PushItem
]
# A partially applied type handler callable
PartialTypeHandler = Callable[[StagingLeafDir, StagingMetadata], Sequence[PushItem_co]]

class TypeHandler(object):
    HANDLERS: Final[ClassVar[MutableMapping[str, UnboundTypeHandlerDelegate]]]
    type_name: str
    def __init__(self, type_name: str) -> None: ...
    def __call__(self, fn: UnboundTypeHandlerDelegate) -> None: ...

class StagedBaseMixin(object):
    _FILE_TYPES = Final[ClassVar[MutableMapping[str, PartialTypeHandler]]]
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __mixin_push_items(
        self,
        leafdir: StagingLeafDir,
        metadata: StagingMetadata,
        delegate: BoundTypeHandlerDelegate,
    ) -> Sequence[PushItem_co]: ...
