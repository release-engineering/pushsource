import pytest

from pushsource import (
    ContainerImagePullSpec,
    ContainerImageTagPullSpec,
    ContainerImageDigestPullSpec,
    ContainerImagePullInfo,
)


def test_invalid_spec():
    """Can't create a ContainerImagePullSpec from an invalid string."""

    with pytest.raises(ValueError):
        ContainerImagePullSpec._from_str("this ain't no pull spec")


def test_wrong_spec_type():
    """Can't put tag specs in digest_specs and vice-versa"""

    tag_spec = ContainerImageTagPullSpec(
        registry="example.com", repository="my-repo", tag="quux"
    )
    digest_spec = ContainerImageDigestPullSpec(
        registry="example.com",
        repository="my-repo",
        digest="sha256:7d5d0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
    )

    with pytest.raises(TypeError):
        ContainerImagePullInfo(tag_specs=[tag_spec], digest_specs=[tag_spec])

    with pytest.raises(TypeError):
        ContainerImagePullInfo(tag_specs=[digest_spec], digest_specs=[digest_spec])


def test_empty_specs():
    """Can't create pull info without at least one tag + digest spec"""

    tag_spec = ContainerImageTagPullSpec(
        registry="example.com", repository="my-repo", tag="quux"
    )
    digest_spec = ContainerImageDigestPullSpec(
        registry="example.com",
        repository="my-repo",
        digest="sha256:7d5d0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
    )

    with pytest.raises(ValueError):
        ContainerImagePullInfo(tag_specs=[], digest_specs=[])

    with pytest.raises(ValueError):
        ContainerImagePullInfo(tag_specs=[tag_spec], digest_specs=[])

    with pytest.raises(ValueError):
        ContainerImagePullInfo(tag_specs=[], digest_specs=[digest_spec])

    # If I provide both, it should work
    ContainerImagePullInfo(tag_specs=[tag_spec], digest_specs=[digest_spec])


def test_digest_spec_for_type():
    """digest_spec_for_type looks up spec by type correctly"""

    tag_spec = ContainerImageTagPullSpec(
        registry="example.com", repository="my-repo", tag="quux"
    )
    digest_spec_v1 = ContainerImageDigestPullSpec(
        registry="example.com",
        repository="my-repo",
        digest="sha256:7d5d0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
        media_type="application/vnd.docker.distribution.manifest.v1+json",
    )
    digest_spec_v2 = ContainerImageDigestPullSpec(
        registry="example.com",
        repository="my-repo",
        digest="sha256:aaad0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
        media_type="application/vnd.docker.distribution.manifest.v2+json",
    )

    pull_info = ContainerImagePullInfo(
        tag_specs=[tag_spec], digest_specs=[digest_spec_v1, digest_spec_v2]
    )

    # Can get those specs by media type
    assert (
        pull_info.digest_spec_for_type(
            "application/vnd.docker.distribution.manifest.v1+json"
        )
        == digest_spec_v1
    )
    assert (
        pull_info.digest_spec_for_type(
            "application/vnd.docker.distribution.manifest.v2+json"
        )
        == digest_spec_v2
    )

    # Can get None for other arbitrary types
    assert (
        pull_info.digest_spec_for_type(
            "application/vnd.docker.distribution.manifest.list.v2+json"
        )
        is None
    )
    assert pull_info.digest_spec_for_type("whatever-type") is None
