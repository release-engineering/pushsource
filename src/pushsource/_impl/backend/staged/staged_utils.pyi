from collections import Mapping
from typing import Final, Any, Optional, NoReturn, Union

from pushsource._impl.validator import Validator
from pushsource._impl.type_aliases import JsonObject

REQUIRED_VERSION: Final[str] = ...
VALIDATOR: Final[Validator] = ...

class StagingFileMetadata(object):
    attributes: Mapping[Any]
    filename: str
    relative_path: str
    sha256sum: str
    version: str
    def __init__(
        self,
        attributes: Mapping[Any],
        filename: str,
        relative_path: str,
        sha256sum: str,
        version: str,
    ) -> None: ...

class StagingMetadata(object):
    filename: Optional[str] = ...
    file_metadata: Optional[Mapping[str, StagingFileMetadata]] = ...
    def __init__(
        self,
        filename: Optional[str] = ...,
        file_metadata: Optional[Mapping[str, StagingFileMetadata]] = ...,
    ) -> None: ...
    def file_metadata_or_die(self, relative_path: str) -> StagingFileMetadata: ...
    @classmethod
    def from_data(cls, data: JsonObject, filename: str = ...) -> "StagingMetadata": ...

class StagingLeafDir(object):
    file_type: str
    dest: str
    path: str
    topdir: str
    def __init__(
        self,
        file_type: str,
        dest: str,
        path: str,
        topdir: str,
    ) -> None: ...
