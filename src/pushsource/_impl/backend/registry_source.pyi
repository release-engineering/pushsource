from collections import Iterator
from re import Pattern
from types import TracebackType
from typing import Optional, Type

from pushsource import Source, PushItem
from pushsource._impl.model.base import PushItem_co
from pushsource.type_aliases import MaybeString

IMAGE_URI_REGEX: Pattern

class RegistrySource(Source):
    def __init__(
        self,
        image: MaybeString,
        dest: Optional[MaybeString] = ...,
        dest_signing_key: Optional[MaybeString] = ...,
    ) -> None: ...
    def __enter__(self) -> "RegistrySource": ...
    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None: ...
    def __iter__(self) -> Iterator[PushItem_co]: ...
    def _push_item_from_registry_uri(self, uri: str, signing_key: str) -> PushItem: ...
