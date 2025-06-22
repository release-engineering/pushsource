import xmlrpc.client
from collections import Sequence
from typing import Any, TypeVar

from pushsource._impl.type_aliases import JsonObject

ErrataRaw_co = TypeVar("ErrataRaw_co", bound="ErrataRaw", covariant=True)

class ErrataRaw(object):
    advisory_cdn_metadata: JsonObject
    advisory_cdn_file_list: JsonObject
    advisory_cdn_docker_file_list: JsonObject
    ftp_paths: JsonObject
    def __init__(
        self,
        advisory_cdn_metadata: JsonObject,
        advisory_cdn_file_list: JsonObject,
        advisory_cdn_docker_file_list: JsonObject,
        ftp_paths: JsonObject,
    ) -> None: ...

class ErrataClient(object):
    _errata_service: xmlrpc.client.ServerProxy
    def __init__(self, threads: int, url: str, **retry_args: Any) -> None: ...
    def shutdown(self) -> None: ...
    def _log_queried_et(self, response: JsonObject, advisory_id: str) -> JsonObject: ...
    def get_raw_f(self, advisory_id: str) -> Sequence[ErrataRaw_co]: ...
    # TODO: narrow return type if possible: JsonObject maybe?
    def _call_et(self, method_name: str, advisory_id: str) -> Any: ...
