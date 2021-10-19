import os

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from pytest import raises

from pushsource import (
    Source,
    RegistrySource,
    ContainerImagePushItem,
    SourceContainerImagePushItem,
)


MANIFEST_V2SCH2 = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "size": 7023,
        "digest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f432a537bc7",
    },
    "layers": [
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 32654,
            "digest": "sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f",
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 16724,
            "digest": "sha256:3c3a4604a545cdc127456d94e421cd355bca5b528f4a9c1905b15da2eb4a4c6b",
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 73109,
            "digest": "sha256:ec4b8955958665577945c89419d1af06b5f7636b4ac3da7f12184802ad867736",
        },
    ],
}

MANIFEST_V2LIST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "manifests": [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 7143,
            "digest": "sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f",
            "platform": {
                "architecture": "ppc64le",
                "os": "linux",
            },
        },
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 7682,
            "digest": "sha256:5b0bcabd1ed22e9fb1310cf6c2dec7cdef19f0ad69efa1f392e94a4333501270",
            "platform": {"architecture": "amd64", "os": "linux", "features": ["sse4"]},
        },
    ],
}


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items."""

    mocked_get_manifest.side_effect = [
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest=["repo1", "repo2"],
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest:dest-latest",
            "https://registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1:dest-1.1",
        ],
        signing_key="1234abcde",
    )
    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 2
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == ["repo1:dest-latest", "repo2:dest-latest"]

    assert (
        items[1].name
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert (
        items[1].src
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert items[1].dest_signing_key == "1234abcde"
    assert items[1].source_tags == ["1.1"]
    assert items[1].dest == ["repo1:dest-1.1", "repo2:dest-1.1"]


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_multiple_signing_keys(
    mocked_inspect,
    mocked_get_manifest
):
    """Registry source yield push items for multiple signing keys."""

    mocked_get_manifest.side_effect = [
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest="repo",
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest:dest-latest",
            "https://registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1:dest-1.1",
        ],
        signing_key=["1234abcde", "56784321"],
    )
    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 4
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest", items[
        0
    ].name
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == ["repo:dest-latest"]

    assert (
        items[1].name
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert (
        items[1].src
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert items[1].dest_signing_key == "1234abcde"
    assert items[1].source_tags == ["1.1"]
    assert items[1].dest == ["repo:dest-1.1"]

    assert items[2].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest", items[
        1
    ].name
    assert items[2].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[2].dest_signing_key == "56784321"
    assert items[2].source_tags == ["latest"]
    assert items[2].dest == ["repo:dest-latest"]

    assert (
        items[3].name
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert (
        items[3].src
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert items[3].dest_signing_key == "56784321"
    assert items[3].source_tags == ["1.1"]
    assert items[3].dest == ["repo:dest-1.1"]


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_invalid(
    mocked_inspect,
    mocked_get_manifest
):
    """Registry source raises value error due to invalid push items"""

    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    mocked_get_manifest.side_effect = [
        (
            "application/json",
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
    ]
    source = RegistrySource(
        dest="pulp",
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest:dest-latest",
        ],
        signing_key="1234abcde",
    )
    # Eagerly fetch
    with raises(ValueError) as exc_info:
        with source:
            items = list(source)
    assert str(exc_info.value) == "Unsupported manifest type:application/json"


@patch("pushsource._impl.backend.registry_source.get_manifest")
def test_registry_push_items_missing_dest_tag(
    mocked_get_manifest
):
    """Registry source raises value error due to invalid push items"""

    mocked_get_manifest.side_effect = [
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
    ]
    source = RegistrySource(
        dest="pulp",
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest",
        ],
        signing_key="1234abcde",
    )
    # Eagerly fetch
    with raises(ValueError) as exc_info:
        with source:
            items = list(source)
    assert "At least one dest tag is required for" in str(exc_info.value)



@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_source_get(mocked_inspect, mocked_get_manifest):
    """Get registry source based on prefix and test generated push items."""

    mocked_get_manifest.side_effect = [
        (
            "application/vnd.docker.distribution.manifest.v1+json",
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "test-digest-2",
            MANIFEST_V2LIST,
        ),
        (
            "application/vnd.docker.distribution.manifest.v2+json",
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
    ]
    source = Source.get(
        "registry:",
        dest="pulp",
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest:latest",
            "https://registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1:1.1",
            "https://registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1-src:1.1-src",
        ],
        signing_key="1234abcde",
    )

    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-3", "config": {}, 'source': True},
    ]

    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 3
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]

    assert (
        items[1].name
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert (
        items[1].src
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1"
    )
    assert items[1].dest_signing_key == "1234abcde"
    assert items[1].source_tags == ["1.1"]

    assert (
        items[2].name
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1-src"
    )
    assert (
        items[2].src
        == "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1-src"
    )
    assert items[2].dest_signing_key == "1234abcde"
    assert items[2].source_tags == ["1.1-src"]


def test_registry_push_items_missing_dest():
    """Registry source yield push items."""

    source = RegistrySource(
        dest=["repo1", "repo2"],
        registry_uris=[
            "https://registry.redhat.io/odf4/mcg-operator-bundle:latest",
        ],
        signing_key="1234abcde",
    )
    # Eagerly fetch
    with source:
        with raises(
            ValueError,
            match="https://registry.redhat.io/odf4/mcg-operator-bundle:latest",
        ):
            items = list(source)
