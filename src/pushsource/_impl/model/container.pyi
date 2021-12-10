from collections import Sequence, Mapping
from typing import Text, AnyStr, TypeVar, Optional, Type

from pushsource import PushItem

PullSpec_co = TypeVar("PullSpec_co", bound="ContainerImagePullSpec", covariant=True)
PullSpec_contra = TypeVar(
    "PullSpec_contra", bound="ContainerImagePullSpec", contravariant=True
)

class ContainerImagePullSpec(object):
    registry: Text
    repository: Text
    @classmethod
    def _from_str(cls, pull_spec: AnyStr) -> PullSpec_co: ...

class ContainerImageTagPullSpec(ContainerImagePullSpec):
    tag: Text
    media_types: Sequence[Text]

class ContainerImageDigestPullSpec(ContainerImagePullSpec):
    digest: Text
    media_type: Optional[Text] = ...

def specs_converter(
    specs: Sequence[PullSpec_contra], expected_class: Type
) -> Sequence[PullSpec_co]: ...
def tag_specs_converter(
    specs: Sequence[PullSpec_contra],
) -> Sequence[ContainerImageTagPullSpec]: ...
def digest_specs_converter(
    specs: Sequence[PullSpec_contra],
) -> Sequence[ContainerImageDigestPullSpec]: ...

class ContainerImagePullInfo(object):
    tag_specs: Sequence[ContainerImageTagPullSpec]
    digest_specs: Sequence[ContainerImageDigestPullSpec]
    media_types: Sequence[Text] = ...
    def digest_spec_for_type(
        self, media_type: Text
    ) -> Optional[ContainerImageDigestPullSpec]: ...

class ContainerImagePushItem(PushItem):
    dest_signing_key: Optional[Text] = ...
    source_tags: Sequence[Text] = ...
    labels: Mapping[Text, Text] = ...
    arch: Optional[Text] = ...
    pull_info: Optional[ContainerImagePullInfo] = ...

class SourceContainerImagePushItem(ContainerImagePushItem): ...
class OperatorManifestPushItem(PushItem): ...
