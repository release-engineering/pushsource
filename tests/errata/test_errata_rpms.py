import os
import pytest
from mock import patch

from pushsource import (
    Source,
    ErratumPushItem,
    ErratumPackage,
    ErratumPackageCollection,
    ErratumReference,
    RpmPushItem,
)

TEST_DATA = (
    ("RHSA-2020:0509", "fd431d51"),
    ("RHSA-2020:0509-sig-key-alias", "foo,bar,baz"),
)

@pytest.mark.parametrize("erratum, expected_sig_key_path", TEST_DATA)
@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_rpms_via_koji(mock_get_rpm_header, mock_get_keys_from_headers, fake_errata_tool, erratum, expected_sig_key_path, fake_koji, koji_dir):
    """Errata source yields RPMs taken from koji source"""

    source = Source.get(
        "errata:https://errata.example.com",
        errata=erratum,
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
        "id": 1234,
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "nvr": "sudo-1.8.25p1-4.el8_0.3",
    }

    # Make signed RPMs exist (contents not relevant here)
    for filename, rpm in fake_koji.rpm_data.items():
        signed_rpm_path = os.path.join(
            koji_dir,
            "packages/sudo/1.8.25p1/4.el8_0.3/",
            "data/signed/%s/%s/%s" % (expected_sig_key_path, rpm["arch"], filename),
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
            name="",
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
                    reboot_suggested=True,
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

    # Erratum should be sent to every dest referenced by an RPM
    rpm_dests = []
    for item in rpm_items:
        rpm_dests.extend(item.dest)
    assert set(errata_item.dest) == set(rpm_dests)

    # It should have found the RPMs referenced by the advisory
    assert sorted(rpm_items, key=lambda rpm: rpm.src) == [
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/ppc64le/sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ),
            dest=["rhel-8-for-ppc64le-baseos-e4s-rpms__8_DOT_0"],
            md5sum="0d56f302617696d3511e71e1669e62c0",
            sha256sum="31c4f73af90c6d267cc5281c59e4a93ae3557b2253d9a8e3fef55f3cafca6e54",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/ppc64le/sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ),
            dest=["rhel-8-for-ppc64le-baseos-e4s-debug-rpms__8_DOT_0"],
            md5sum="e242826fb38f487502cdc1f1a06991d2",
            sha256sum="04db0c39efb31518ff79bf98d1c27256d46cdc72b967a5b2094a6efec3166df2",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/ppc64le/sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ),
            dest=["rhel-8-for-ppc64le-baseos-e4s-debug-rpms__8_DOT_0"],
            md5sum="e242826fb38f487502cdc1f1a06991d2",
            sha256sum="04db0c39efb31518ff79bf98d1c27256d46cdc72b967a5b2094a6efec3166df2",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/ppc64le/sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ),
            dest=["rhel-8-for-ppc64le-baseos-e4s-debug-rpms__8_DOT_0"],
            md5sum="d6da7e2e3d9efe050fef2e8d047682be",
            sha256sum="355cbb9dc348b17782cff57120391685d6a1f6884facc54fac4b7fb54abeffba",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/ppc64le/sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ),
            dest=["rhel-8-for-ppc64le-baseos-e4s-debug-rpms__8_DOT_0"],
            md5sum="d6da7e2e3d9efe050fef2e8d047682be",
            sha256sum="355cbb9dc348b17782cff57120391685d6a1f6884facc54fac4b7fb54abeffba",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.src.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/src/sudo-1.8.25p1-4.el8_0.3.src.rpm",
            ),
            dest=[
                "rhel-8-for-ppc64le-baseos-e4s-source-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-e4s-source-rpms__8_DOT_0",
            ],
            md5sum="f94ab3724b498e3faeab643fe2a67c9c",
            sha256sum="10d7724302a60d0d2ca890fc7834b8143df55ba1ce0176469ea634ac4ab7aa28",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/sudo/1.8.25p1/4.el8_0.3/data/signed",
                f"{expected_sig_key_path}/x86_64/sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
            ),
            dest=["rhel-8-for-x86_64-baseos-e4s-rpms__8_DOT_0"],
            md5sum="25e9470c4fe96034fe1d7525c04b5d8e",
            sha256sum="593f872c1869f7beb963c8df2945fc691a1d999945c8c45c6bc7e02731fa016f",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="fd431d51",
        ),
    ]
