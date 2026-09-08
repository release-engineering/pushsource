from collections import Mapping, Sequence
from typing import Final, Any

from pushsource import ContainerImagePullInfo
from pushsource._impl.model.container import ContainerImagePullSpec_co

MIME_TYPE_MANIFEST_LIST: Final[str] = ...

# TODO: a lot of the properties of this class are ambiguous
#  Mapping[Any] (i.e. Mapping[Any, Any]): can this be narrowed?
#  Perhaps the JsonObject type would be more helpful.
class ContainerArchiveHelper(object):
    build_image: Mapping[Any]
    build_index: Mapping[Any]
    archive_extra: Mapping[Any]
    archive_docker: Mapping[Any]
    source_tags: Sequence[str]
    arch: str
    labels: Mapping[Any]
    pull_info: ContainerImagePullInfo

def get_tag_specs(raw_specs: Sequence[str]) -> Sequence[ContainerImagePullSpec_co]: ...
def get_digest_specs(raw_specs: Sequence[str], digests_map):
    Sequence[ContainerImagePullSpec_co]: ...
