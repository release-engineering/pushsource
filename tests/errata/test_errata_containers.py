import os
from mock import patch
import json

import pytest

from pushsource import Source, ContainerImagePushItem, OperatorManifestPushItem

@pytest.fixture(autouse=True)
def baseline_errata_requests_mock(errata_requests_mock):
    yield

@pytest.fixture(autouse=True)
def fake_kerberos_auth(mocker):
    mocker.patch("gssapi.Name")
    mocker.patch("gssapi.Credentials.acquire")
    mocker.patch("requests_gssapi.HTTPSPNEGOAuth", return_value=None)

@pytest.fixture
def source_factory(fake_errata_tool, fake_koji, koji_dir):
    ctor = Source.get_partial(
        "errata:https://errata.example.com",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    fake_koji.load_all_builds()

    yield ctor


def test_errata_containers_no_repos(source_factory, koji_dir):
    """Errata source fails to retrieve container-related push items if ET requests no repos"""

    source = source_factory(errata="RHBA-2020:2807-no-repos")

    # It should fail
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # And tell us why
    assert (
        "Erratum RHBA-2020:2807 requests container build "
        "cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1 "
        "but provides no repositories"
    ) in str(exc_info)


def test_errata_containers_missing_build(source_factory, fake_koji):
    """Errata source gives an error if a requested container build is missing"""

    fake_koji.remove_build(
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    )

    source = source_factory(errata="RHBA-2020:2807")

    # It should raise
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us why
    assert (
        "Container image build not found in koji: "
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ) in str(exc_info)


@patch("pushsource._impl.source.os.path.exists")
def test_errata_ignores_unknown_koji_types(mock_path_exists, source_factory, koji_dir):
    """Errata source, when requesting containers, will skip unknown push item types
    yielded by koji source."""

    # This is a very niche case, but to get that 100% coverage...
    # It's possible that koji_source might produce something other than ContainerImagePushItem
    # or OperatorManifestPushItem, and we want to be forwards-compatible with that.

    # This is our hacked source which returns whatever koji returns, but also some
    # arbitrary objects
    class WeirdKoji(object):
        def __init__(self, **kwargs):
            # Get a normal koji source...
            self.koji = Source.get(
                "koji:https://koji.example.com?basedir=%s" % koji_dir, **kwargs
            )

        def __iter__(self):
            # We'll yield whatever koji yields but surround it with
            # unexpected junk
            yield object()
            for item in self.koji:
                yield item
            yield object()

    mock_path_exists.return_value = True
    Source.register_backend("weird-koji", WeirdKoji)

    source = source_factory(errata="RHBA-2020:2807", koji_source="weird-koji:")

    # It should still work as normal
    items = list(source)

    # Sanity check we got the right number of items
    assert len(items) == 45


def test_errata_containers_missing_image_meta(source_factory, fake_koji):
    """Errata source gives an error if a requested container build exists but
    image data is missing from build.
    """

    build = fake_koji.build_data[
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ]
    del build["extra"]

    source = source_factory(errata="RHBA-2020:2807")

    # It should raise
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us why
    assert (
        "Build elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1 "
        "not recognized as a container image build"
    ) in str(exc_info)


def test_errata_containers_broken_multiarch(source_factory, fake_koji):
    """Errata source gives an error if a requested container build exists, has multiple
    image archives and misses the manifest list mimetype in metadata.
    """

    build = fake_koji.build_data[
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ]
    del build["extra"]["typeinfo"]["image"]["media_types"]

    source = source_factory(errata="RHBA-2020:2807")

    # It should raise
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us why
    assert (
        "Could not find (exactly) one container image archive on koji build "
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ) in str(exc_info)


def test_errata_containers_broken_operator_reference(source_factory, fake_koji):
    """Errata source gives an error if a requested container build exists and points
    at an operator archive, but the archive is missing from koji.
    """

    fake_koji.remove_archive(
        "operator_manifests.zip",
        "cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
    )

    source = source_factory(errata="RHBA-2020:2807")

    # It should raise
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us why
    assert (
        "koji build cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1 "
        'metadata refers to missing operator-manifests archive "operator_manifests.zip"'
    ) in str(exc_info)


def test_errata_containers_multi_sig_key(source_factory, fake_koji):
    """Errata source gives an error if Errata Tool requests push of a single image with
    multiple signing keys.
    """

    source = source_factory(errata="RHBA-2020:2807-sig-key-conflict")

    # It should raise
    with pytest.raises(ValueError) as exc_info:
        list(source)

    # It should tell us why
    assert (
        "Unsupported: erratum RHBA-2020:2807 requests multiple signing keys "
        "(199e2f91fd431d51, 222e2f91fd431d51) on build "
        "cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ) in str(exc_info)
