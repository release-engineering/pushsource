import os

import pytest

from pushsource import Source, ContainerImagePushItem, OperatorManifestPushItem


@pytest.fixture
def source_factory(fake_errata_tool, fake_koji, koji_dir):
    ctor = Source.get_partial(
        "errata:https://errata.example.com",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    for nvr in [
        "elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "local-storage-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "openshift-enterprise-ansible-service-broker-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "openshift-enterprise-template-service-broker-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "ose-metering-ansible-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "ose-ptp-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
        "sriov-network-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
    ]:
        fake_koji.load_build(nvr)

    # Tweak this one build to have legacy reference to operator_manifests_archive
    # to prove that this still works.
    build = fake_koji.build_data[
        "cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ]
    extra = build["extra"]
    extra["operator_manifests_archive"] = extra["typeinfo"]["operator-manifests"].pop(
        "archive"
    )

    # And tweak this one to not have any operator archive at all to prove this works too.
    build = fake_koji.build_data[
        "sriov-network-operator-metadata-container-v4.3.28.202006290519.p0.prod-1"
    ]
    extra = build["extra"]
    del extra["typeinfo"]["operator-manifests"]

    yield ctor


def test_errata_containers(source_factory, koji_dir):
    """Errata source can be used to retrieve container-related push items,
    typical scenario"""

    source = source_factory(errata="RHBA-2020:2807")

    items = list(source)
    items = sorted(items, key=lambda item: item.name)

    image_items = [i for i in items if isinstance(i, ContainerImagePushItem)]
    operator_items = [i for i in items if isinstance(i, OperatorManifestPushItem)]

    # Helper to make 'src' attributes below a bit less cumbersome
    def koji_path(*args):
        return os.path.join(koji_dir, *args)

    # This is quite a large set of very similar images. We'll only do a full check on the first few
    # to avoid the test becoming huge.
    assert image_items[0:4] == [
        ContainerImagePushItem(
            name="docker-image-sha256:05db9dc3ed76f6cf993f0dd35aa51892a38ba51afdf8ed564a236d53d8375a47.x86_64.tar.gz",
            state="PENDING",
            src=koji_path(
                "packages/sriov-network-operator-metadata-container/v4.3.28.202006290519.p0.prod/1/images",
                "docker-image-sha256:05db9dc3ed76f6cf993f0dd35aa51892a38ba51afdf8ed564a236d53d8375a47.x86_64.tar.gz",
            ),
            dest=[
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3",
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
            ],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="sriov-network-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        ContainerImagePushItem(
            name="docker-image-sha256:088c14ddcc989815bb38871fe9e0d3387a762c07a2ca23c9fd375ce42e3e53d6.ppc64le.tar.gz",
            state="PENDING",
            src=koji_path(
                "packages/elasticsearch-operator-metadata-container/v4.3.28.202006290519.p0.prod/1/images",
                "docker-image-sha256:088c14ddcc989815bb38871fe9e0d3387a762c07a2ca23c9fd375ce42e3e53d6.ppc64le.tar.gz",
            ),
            dest=[
                "openshift4/ose-elasticsearch-rhel7-operator-metadata:v4.3",
                "openshift4/ose-elasticsearch-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
                "openshift4/ose-elasticsearch-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
            ],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        ContainerImagePushItem(
            name="docker-image-sha256:115387bd7efba2bdb7ee9f0d4fff88f03c1579859c6230cc67bb5c0b31263ba8.ppc64le.tar.gz",
            state="PENDING",
            src=koji_path(
                "packages/sriov-network-operator-metadata-container/v4.3.28.202006290519.p0.prod/1/images",
                "docker-image-sha256:115387bd7efba2bdb7ee9f0d4fff88f03c1579859c6230cc67bb5c0b31263ba8.ppc64le.tar.gz",
            ),
            dest=[
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3",
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
                "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
            ],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="sriov-network-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        ContainerImagePushItem(
            name="docker-image-sha256:176277a797bafa67823741efa319c2844758b2d5a4cb796b75a8b67580b54d56.aarch64.tar.gz",
            state="PENDING",
            src=koji_path(
                "packages/ose-metering-ansible-operator-metadata-container/v4.3.28.202006290519.p0.prod/1/images",
                "docker-image-sha256:176277a797bafa67823741efa319c2844758b2d5a4cb796b75a8b67580b54d56.aarch64.tar.gz",
            ),
            dest=[
                "openshift4/ose-metering-ansible-rhel7-operator-metadata:v4.3",
                "openshift4/ose-metering-ansible-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
                "openshift4/ose-metering-ansible-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
            ],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="ose-metering-ansible-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
    ]

    # Similarly for operators.
    assert operator_items[0:4] == [
        OperatorManifestPushItem(
            name="cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1/operator_manifests.zip",
            state="PENDING",
            src=koji_path(
                "packages/cluster-logging-operator-metadata-container",
                "v4.3.28.202006290519.p0.prod/1/files",
                "operator-manifests/operator_manifests.zip",
            ),
            # Note that operators don't have any 'dest' assigned.
            dest=[],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="cluster-logging-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        OperatorManifestPushItem(
            name="cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1/operator_manifests.zip",
            state="PENDING",
            src=koji_path(
                "packages/cluster-nfd-operator-metadata-container",
                "v4.3.28.202006290519.p0.prod/1/files",
                "operator-manifests/operator_manifests.zip",
            ),
            dest=[],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="cluster-nfd-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        OperatorManifestPushItem(
            name="elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1/operator_manifests.zip",
            state="PENDING",
            src=koji_path(
                "packages/elasticsearch-operator-metadata-container",
                "v4.3.28.202006290519.p0.prod/1/files",
                "operator-manifests/operator_manifests.zip",
            ),
            dest=[],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="elasticsearch-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
        OperatorManifestPushItem(
            name="local-storage-operator-metadata-container-v4.3.28.202006290519.p0.prod-1/operator_manifests.zip",
            state="PENDING",
            src=koji_path(
                "packages/local-storage-operator-metadata-container",
                "v4.3.28.202006290519.p0.prod/1/files",
                "operator-manifests/operator_manifests.zip",
            ),
            dest=[],
            md5sum=None,
            sha256sum=None,
            origin="RHBA-2020:2807",
            build="local-storage-operator-metadata-container-v4.3.28.202006290519.p0.prod-1",
            signing_key=None,
        ),
    ]


def test_errata_legacy_repos(source_factory):
    """Errata source can make use of legacy repo IDs as needed"""
    source1 = source_factory(errata="RHBA-2020:2807")
    source2 = source_factory(errata="RHBA-2020:2807", legacy_container_repos=True)

    items1 = sorted(
        [i for i in source1 if isinstance(i, ContainerImagePushItem)],
        key=lambda i: i.name,
    )
    items2 = sorted(
        [i for i in source2 if isinstance(i, ContainerImagePushItem)],
        key=lambda i: i.name,
    )

    # OK, we've got two lists of push items generated identically except that one requested
    # legacy repos and the other didn't. Let's sample the first push item to see how they differ.

    assert items1[0].dest == [
        # This is the preferred format.
        "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3",
        "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
        "openshift4/ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
    ]

    assert items2[0].dest == [
        # This is the weird legacy stuff.
        "redhat-openshift4-ose-sriov-network-rhel7-operator-metadata:v4.3",
        "redhat-openshift4-ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod",
        "redhat-openshift4-ose-sriov-network-rhel7-operator-metadata:v4.3.28.202006290519.p0.prod-1",
    ]


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


def test_errata_ignores_unknown_koji_types(source_factory, koji_dir):
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
