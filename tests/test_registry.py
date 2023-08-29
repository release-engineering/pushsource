import os

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from pytest import raises
import requests

from pushsource import (
    Source,
    RegistrySource,
    ContainerImagePushItem,
    SourceContainerImagePushItem,
)
from pushsource._impl.utils.containers import (
    MEDIATYPE_SCHEMA2_V1,
    MEDIATYPE_SCHEMA2_V1_SIGNED,
    MEDIATYPE_SCHEMA2_V2,
    MEDIATYPE_SCHEMA2_V2_LIST,
)


MANIFEST_V2SCH2 = {
    "schemaVersion": 2,
    "mediaType": MEDIATYPE_SCHEMA2_V2,
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

MANIFEST_V1 = {
    "schemaVersion": 1,
    "tag": "latest",
    "name": "odf4/mcg-operator-bundle",
    "architecture": "amd64",
    "fsLayers": [
        {
            "blobSum": "sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4"
        },
        {
            "blobSum": "sha256:5eb901baf1071ec7a95a08034275fd23d9c776f2f066e18bf9c159c63a21f67a"
        },
    ],
    "history": [],
}

MANIFEST_V2LIST = {
    "schemaVersion": 2,
    "mediaType": MEDIATYPE_SCHEMA2_V2_LIST,
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

    response_404 = requests.Response()
    response_404.status_code = 404
    mocked_get_manifest.side_effect = [
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        requests.exceptions.HTTPError(response=response_404),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-2",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-2",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest=["repo1", "repo2"],
        image=[
            "registry.redhat.io/odf4/mcg-operator-bundle:latest",
            "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1",
        ],
        dest_signing_key="1234abcde",
        product_name="test-product",
    )
    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 2
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == ["repo1", "repo2"]
    assert items[0].product_name == "test-product"

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
    assert items[1].dest == ["repo1", "repo2"]
    assert items[1].product_name == "test-product"


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_500_raises(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items."""

    response_500 = requests.Response()
    response_500.status_code = 500
    mocked_get_manifest.side_effect = [
        requests.exceptions.HTTPError(response=response_500),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest=["repo1"],
        image=["registry.redhat.io/odf4/mcg-operator-bundle:latest"],
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with raises(requests.exceptions.HTTPError):
        with source:
            items = list(source)

    mocked_get_manifest.side_effect = [
        requests.exceptions.RetryError("Application error", response=response_500),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]
    source = RegistrySource(
        dest=["repo1"],
        image=["registry.redhat.io/odf4/mcg-operator-bundle:latest"],
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with raises(requests.exceptions.RetryError):
        with source:
            items = list(source)


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_tolerate_404_retries(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items."""

    response_404 = requests.Response()
    response_404.status_code = 404
    mocked_get_manifest.side_effect = [
        requests.exceptions.RetryError(
            "too many 404 error responses", response=response_404
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest=[
            "repo1",
        ],
        image=[
            "registry.redhat.io/odf4/mcg-operator-bundle:latest",
        ],
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with source:
        items = list(source)


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_no_signing_key(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items."""

    mocked_get_manifest.side_effect = [
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-2",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-2",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        image="registry.redhat.io/odf4/mcg-operator-bundle:latest",
    )
    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 1
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == None
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == []


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_no_dest(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items."""

    mocked_get_manifest.side_effect = [
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-2",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-2",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        image="registry.redhat.io/odf4/mcg-operator-bundle:latest",
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 1
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == []


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_multiple_signing_keys(mocked_inspect, mocked_get_manifest):
    """Registry source yield push items for multiple signing keys."""

    mocked_get_manifest.side_effect = [
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-2",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-2",
            MANIFEST_V2LIST,
        ),
    ]
    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    source = RegistrySource(
        dest="repo",
        image="registry.redhat.io/odf4/mcg-operator-bundle:latest,"
        "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1",
        dest_signing_key=["1234abcde", "56784321"],
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
    assert items[0].dest == ["repo"]

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
    assert items[1].dest == ["repo"]

    assert items[2].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest", items[
        1
    ].name
    assert items[2].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[2].dest_signing_key == "56784321"
    assert items[2].source_tags == ["latest"]
    assert items[2].dest == ["repo"]

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
    assert items[3].dest == ["repo"]


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_invalid(mocked_inspect, mocked_get_manifest):
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
        image="registry.redhat.io/odf4/mcg-operator-bundle:latest:dest-latest",
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with raises(ValueError) as exc_info:
        with source:
            items = list(source)
    assert str(exc_info.value) == "Unsupported manifest type: application/json"


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_registry_push_items_tolerate_text_plain(mocked_inspect, mocked_get_manifest):
    """Registry source raises value error due to invalid push items"""

    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
    ]

    mocked_get_manifest.side_effect = [
        (
            "text/plain",
            "test-digest-1-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1-2",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1-3",
            MANIFEST_V2LIST,
        ),
    ]
    source = RegistrySource(
        dest="pulp",
        image="registry.redhat.io/odf4/mcg-operator-bundle:latest",
        dest_signing_key="1234abcde",
    )
    # Eagerly fetch
    with source:
        items = list(source)
    assert len(items) == 1
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest", items[
        0
    ].name
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == ["pulp"]
    assert [x.media_type for x in items[0].pull_info.digest_specs] == [
        MEDIATYPE_SCHEMA2_V2_LIST,
        MEDIATYPE_SCHEMA2_V2,
        MEDIATYPE_SCHEMA2_V1,
    ]


@patch("pushsource._impl.backend.registry_source.get_manifest")
@patch("pushsource._impl.backend.registry_source.inspect")
def test_source_get(mocked_inspect, mocked_get_manifest):
    """Get registry source based on prefix and test generated push items."""

    mocked_get_manifest.side_effect = [
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V1,
            "test-digest-1",
            MANIFEST_V1,
        ),
        (
            MEDIATYPE_SCHEMA2_V2,
            "test-digest-1",
            MANIFEST_V2SCH2,
        ),
        (
            MEDIATYPE_SCHEMA2_V2_LIST,
            "test-digest-1",
            MANIFEST_V2LIST,
        ),
    ]
    source = Source.get(
        "registry:?image=registry.redhat.io/odf4/mcg-operator-bundle:latest,"
        "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1,"
        "registry.redhat.io/openshift/serverless-1-net-istio-controller-rhel8:1.1-src"
        "&dest=repo1,repo2&dest_signing_key=1234abcde"
    )

    mocked_inspect.side_effect = [
        {"digest": "test-digest-1", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-2", "config": {"labels": {"architecture": "amd64"}}},
        {"digest": "test-digest-3", "config": {}, "source": True},
    ]

    # Eagerly fetch
    with source:
        items = list(source)

    assert len(items) == 3
    assert items[0].name == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].src == "registry.redhat.io/odf4/mcg-operator-bundle:latest"
    assert items[0].dest_signing_key == "1234abcde"
    assert items[0].source_tags == ["latest"]
    assert items[0].dest == ["repo1", "repo2"]

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
    assert items[1].dest == ["repo1", "repo2"]

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
    assert items[2].dest == ["repo1", "repo2"]


def test_source_get_invalid_items():
    """Get registry source with invalid image URIs."""

    source = Source.get("registry:?image=registry.redhat.io/odf4/mcg-operator-bundle")
    with raises(ValueError):
        with source:
            items = list(source)

    source = Source.get(
        "registry:?image=registry.redhat.io/odf4/mcg-operator-bundle@latest:latest"
    )
    with raises(ValueError):
        with source:
            items = list(source)
