from collections import Mapping, Iterator
from collections.abc import Sequence
from types import TracebackType
from typing import Optional, Type, List, Any

from pushsource import (
    Source,
    ErratumPushItem,
    ContainerImagePushItem,
)
from pushsource._impl.backend.errata_source.errata_client import ErrataRaw
from pushsource._impl.model.base import PushItem_co, PushItem_contra
from pushsource._impl.type_aliases import MaybeString

# TODO: is the value type a model type or just a Mapping?
DockerFileList = Mapping[str, Any]

# TODO: is the value type a model type or just a Mapping?
RpmList = Mapping[str, Mapping[Any, ...]]

class ErrataSource(Source):
    _errata_service_url: str
    _advisory_ids: List[str]
    def __init__(
        self,
        url: str,
        errata: MaybeString,
        koji_source: Optional[str] = ...,
        rpm_filter_arch: Optional[MaybeString] = ...,
        legacy_container_repos: bool = ...,
        threads: int = ...,
        timeout: int = ...,
    ) -> None: ...
    def __enter__(self) -> "ErrataSource": ...
    def __exit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None: ...
    def __iter__(self) -> Iterator[PushItem_co]: ...
    def _koji_source(**kwargs: Any) -> Source: ...
    def _push_items_from_raw(self, raw: ErrataRaw) -> Sequence[PushItem_co]: ...
    def _push_items_from_container_manifests(
        self, erratum: ErratumPushItem, docker_file_list: DockerFileList
    ) -> Sequence[PushItem_co]: ...
    def _enrich_container_push_item(
        self,
        erratum: ErratumPushItem,
        docker_file_list: DockerFileList,
        item: ContainerImagePushItem,
    ) -> ContainerImagePushItem: ...
    def _push_items_from_rpms(
        self, erratum: ErratumPushItem, rpm_list: RpmList
    ) -> Sequence[PushItem_co]: ...
    def _module_push_items_from_build(
        self, erratum: ErratumPushItem, build_nvr: str, build_info: Mapping[Any, ...]
    ) -> Sequence[PushItem_co]: ...
    def _filter_rpms_by_arch(
        self, erratum: ErratumPushItem, rpm_filenames: Sequence[str]
    ) -> Sequence[str]: ...
    def _rpm_push_items_from_build(
        self, erratum: ErratumPushItem, build_nvr: str, build_info: Mapping[Any, ...]
    ) -> Sequence[PushItem_co]: ...
    def _add_ftp_paths(
        self, items: Sequence[PushItem_contra], erratum: ErratumPushItem, raw: ErrataRaw
    ) -> Sequence[PushItem_co]: ...
