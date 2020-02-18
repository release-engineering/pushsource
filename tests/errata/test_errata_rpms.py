import os
from pytest import raises, fixture
from mock import patch

from .fake_errata_tool import FakeErrataToolController
from ..koji.fake_koji import FakeKojiController

from pushsource import (
    Source,
    ErratumPushItem,
    ErratumPackage,
    ErratumPackageCollection,
    ErratumReference,
    RpmPushItem,
)


@fixture
def fake_errata_tool():
    controller = FakeErrataToolController()
    with patch("pushsource._impl.backend.errata_source.ServerProxy") as mock_proxy:
        mock_proxy.side_effect = controller.proxy
        yield controller


@fixture
def fake_koji():
    controller = FakeKojiController()
    with patch("koji.ClientSession") as mock_session:
        mock_session.side_effect = controller.session
        yield controller


@fixture
def koji_dir(tmpdir):
    yield str(tmpdir.mkdir("koji"))


def test_errata_rpms_via_koji(fake_errata_tool, fake_koji, koji_dir):
    """Errata source yields RPMs taken from koji source"""

    source = Source.get(
        "errata:https://errata.example.com",
        errata="RHSA-2020:0509",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    # Insert koji RPMs referenced by this advisory
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.src.rpm"] = {
        "arch": "src",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debuginfo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debuginfo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debugsource",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debugsource",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }

    fake_koji.build_data[1234] = {
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "nvr": "sudo-1.8.25p1-4.el8_0.3",
    }

    signed_rpm_path = os.path.join(
        koji_dir,
        "vol/somevol/packages/foobuild/1.0/1.el8",
        "data/signed/def456/x86_64/foo-1.0-1.x86_64.rpm",
    )

    # Make signed RPMs exist (contents not relevant here)
    for filename, rpm in fake_koji.rpm_data.items():
        signed_rpm_path = os.path.join(
            koji_dir,
            "packages/sudo/1.8.25p1/4.el8_0.3/",
            "data/signed/fd431d51/%s/%s" % (rpm["arch"], filename),
        )
        signed_dir = os.path.dirname(signed_rpm_path)
        if not os.path.exists(signed_dir):
            os.makedirs(signed_dir)
        open(signed_rpm_path, "w")

    items = list(source)

    errata_items = [i for i in items if isinstance(i, ErratumPushItem)]
    rpm_items = [i for i in items if isinstance(i, RpmPushItem)]

    # It should have found the one advisory
    assert len(errata_items) == 1
    errata_item = errata_items[0]

    # Validate a few of the advisory fields
    assert str(errata_item) == "RHSA-2020:0509: Important: sudo security update"

    # pkglist should have just one collection
    assert errata_item.pkglist == [
        ErratumPackageCollection(
            name="RHSA-2020:0509",
            packages=[
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="0d56f302617696d3511e71e1669e62c0",
                    sha1sum=None,
                    sha256sum="31c4f73af90c6d267cc5281c59e4a93ae3557b2253d9a8e3fef55f3cafca6e54",
                ),
                ErratumPackage(
                    arch="SRPMS",
                    filename="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="f94ab3724b498e3faeab643fe2a67c9c",
                    sha1sum=None,
                    sha256sum="10d7724302a60d0d2ca890fc7834b8143df55ba1ce0176469ea634ac4ab7aa28",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="25e9470c4fe96034fe1d7525c04b5d8e",
                    sha1sum=None,
                    sha256sum="593f872c1869f7beb963c8df2945fc691a1d999945c8c45c6bc7e02731fa016f",
                ),
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo-debuginfo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="e242826fb38f487502cdc1f1a06991d2",
                    sha1sum=None,
                    sha256sum="04db0c39efb31518ff79bf98d1c27256d46cdc72b967a5b2094a6efec3166df2",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo-debuginfo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="91126f02975c06015880d6ea99cb2760",
                    sha1sum=None,
                    sha256sum="1b7d3a7613236ffea7c4553eb9dea69fc19557005ac3a059d7e83efc08c5b754",
                ),
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo-debugsource",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="d6da7e2e3d9efe050fef2e8d047682be",
                    sha1sum=None,
                    sha256sum="355cbb9dc348b17782cff57120391685d6a1f6884facc54fac4b7fb54abeffba",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo-debugsource",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="6b0967941c0caf626c073dc7da0272b6",
                    sha1sum=None,
                    sha256sum="43e318fa49e4df685ea0d5f0925a00a336236b2e20f27f9365c39a48102c2cf6",
                ),
            ],
            short="",
            module=None,
        )
    ]
