from collections import Mapping, Callable, Iterator
from types import TracebackType
from typing import Type, TypeVar, Any

from pushsource._impl.model.base import PushItem_co

SourceFactory = Callable[[], "Source"]

# TODO: See the following example from PEP-484 to demonstrate
#  why I think this could be a good idea for Source#get
#  and Source#__enter__ annotations.
#  https://www.python.org/dev/peps/pep-0484/#id33
#  I could easily be convinced that Source can be used
#  in both of those instances without issue.
S = TypeVar("S", bound="Source")

class SourceWrapper(object):
    def __init__(self, delegate: "Source") -> None: ...
    @classmethod
    def _maybe_wrap(cls, delegate: "Source") -> "SourceWrapper": ...

class Source(object):
    _BACKENDS: Mapping[str, SourceFactory]
    _BACKENDS_BUILTIN: Mapping[str, SourceFactory]
    def __enter__(self) -> "Source": ...
    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None: ...
    def __iter__(self) -> Iterator[PushItem_co]: ...
    @classmethod
    def get(cls, source_url: str, **kwargs: Any) -> "Source": ...
    @classmethod
    def get_partial(cls, source_url: str, **kwargs: Any) -> SourceFactory: ...
    @classmethod
    def register_backend(cls, name: str, factory: SourceFactory) -> None: ...
    @classmethod
    def _register_backend_builtin(cls, name: str, factory: SourceFactory) -> None: ...
    @classmethod
    def reset(cls) -> None: ...
