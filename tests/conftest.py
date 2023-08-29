import copy
import os
from pytest import fixture
from mock import patch
import json

from pushsource import Source
from .errata.fake_errata_tool import FakeErrataToolController
from .koji.fake_koji import FakeKojiController
from pushsource._impl.model import (
    ContainerImagePushItem,
    KojiBuildInfo,
    ContainerImagePullInfo,
    ContainerImageTagPullSpec,
    ContainerImageDigestPullSpec,
)

THIS_DIR = os.path.dirname(__file__)
ERRATA_DATA_DIR = os.path.abspath(os.path.join(THIS_DIR, "./errata/data"))

@fixture
def fake_errata_tool():
    controller = FakeErrataToolController()
    with patch(
        "pushsource._impl.backend.errata_source.errata_client.xmlrpc_client.ServerProxy"
    ) as mock_proxy:
        mock_proxy.side_effect = controller.proxy
        yield controller


@fixture
def container_push_item():
    yield ContainerImagePushItem(
        name="docker-image-sha256:da1d6900c5f541a18295f66312cb8d0999aab6f425a6bbccdd2fd8bcc72300f1.aarch64.tar.gz",
        state="PENDING",
        src="/mnt/koji/packages/cluster-logging-operator-metadata-container/v4.3.28.202006290519.p0.prod/1/images/docker-image-sha256:da1d6900c5f541a18295f66312cb8d0999aab6f425a6bbccdd2fd8bcc72300f1.aarch64.tar.gz",
        dest=[],
        md5sum=None,
        sha256sum=None,
        origin=None,
        build="cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        build_info=KojiBuildInfo(
            name="cluster-logging-operator-metadata-container",
            version="v4.3.28.202006290519.p0.prod",
            release="1",
        ),
        signing_key=None,
        dest_signing_key=None,
        source_tags=["rhaos-4.3-rhel-7-candidate-20098-20200707075056-aarch64"],
        labels={
            "com.redhat.build-host": "arm64-osbs-13.prod.osbs.eng.bos.redhat.com",
            "com.redhat.component": "cluster-logging-operator-metadata-container",
            "com.redhat.delivery.appregistry": "true",
            "com.redhat.license_terms": "https://www.redhat.com/en/about/red-hat-end-user-license-agreements",
        },
        arch="arm64",
        pull_info=ContainerImagePullInfo(
            tag_specs=[
                ContainerImageTagPullSpec(
                    registry="registry-proxy.engineering.redhat.com",
                    repository="rh-osbs/openshift-ose-cluster-logging-operator-metadata",
                    tag="v4.3.28.202006290519.p0.prod-1",
                    media_types=[
                        "application/vnd.docker.distribution.manifest.list.v2+json"
                    ],
                ),
                ContainerImageTagPullSpec(
                    registry="registry-proxy.engineering.redhat.com",
                    repository="rh-osbs/openshift-ose-cluster-logging-operator-metadata",
                    tag="rhaos-4.3-rhel-7-candidate-20098-20200707075056-aarch64",
                    media_types=[],
                ),
            ],
            digest_specs=[
                ContainerImageDigestPullSpec(
                    registry="registry-proxy.engineering.redhat.com",
                    repository="rh-osbs/openshift-ose-cluster-logging-operator-metadata",
                    digest="sha256:e38da0971a67c6b3d4261edd9bd679de1be15d0716d208cddf54b0478a73f0a2",
                    media_type="application/vnd.docker.distribution.manifest.list.v2+json",
                ),
                ContainerImageDigestPullSpec(
                    registry="registry-proxy.engineering.redhat.com",
                    repository="rh-osbs/openshift-ose-cluster-logging-operator-metadata",
                    digest="sha256:759da12e95ff57da1e0c83ee534f78a2292b79c1bf288e40ff1cb256d42440a7",
                    media_type="application/vnd.docker.distribution.manifest.v2+json",
                ),
            ],
            media_types=[
                "application/vnd.docker.distribution.manifest.list.v2+json",
                "application/vnd.docker.distribution.manifest.v2+json",
            ],
        ),
    )


@fixture
def fake_koji():
    controller = FakeKojiController()
    with patch("koji.ClientSession") as mock_session:
        mock_session.side_effect = controller.session
        yield controller


@fixture
def koji_dir(tmpdir):
    yield str(tmpdir.mkdir("koji"))

@fixture()
def errata_requests_mock(requests_mock):
    for root, _, files in os.walk(ERRATA_DATA_DIR):
        for filename in files:
            if filename.endswith(".json"):
                path = os.path.join(root, filename)
                with open(path) as fh:
                    data = json.load(fh)
                requests_mock.get(f"/api/v1/erratum/{filename.rstrip('.json')}", json=data)  # nosec B113

    yield

@fixture(autouse=True)
def clean_backends():
    """Reset any modifications of Source._BACKENDS performed during tests."""
    backends = copy.deepcopy(Source._BACKENDS)
    yield
    Source._BACKENDS = backends
