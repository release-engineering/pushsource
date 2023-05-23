import os
import datetime
from mock import patch

import pytest

from pushsource import (
    Source,
    VMIPushItem,
    VMIRelease,
    AmiPushItem,
    AmiRelease,
    VHDPushItem,
    KojiBuildInfo,
)


def test_errata_ami_via_koji(fake_errata_tool, fake_koji, koji_dir):
    """Errata source containing a module yields modules & RPMs taken
    from koji source"""

    source = Source.get(
        "errata:https://errata.example.com",
        errata="RHSA-2022:78146",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    nvr = "rhel-ec2-8.7-1"
    name = "rhel"
    version = "8.7"
    release = "1"

    # Insert some data
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": name,
        "version": version,
        "release": release,
        "nvr": nvr,
        "completion_time": "2022-12-20 12:30:25",
        "extra": {"typeinfo": {"image": {}}},
    }
    fake_koji.build_data[nvr] = fake_koji.build_data[1234]

    imgs = {
        "foo-1.0-20230110.sp.22.raw.xz": "raw-xz",
    }

    archives = []
    for fname, tname in imgs.items():
        archives.append(
            {
                "btype": "image",
                "filename": fname,
                "checksum": "00000000000000000000000000000000",
                "extra": {"image": {"arch": "x86_64"}},
                "type_name": tname,
                "build_id": 1234,
                "nvr": nvr,
            }
        )

    fake_koji.insert_archives(archives=archives, build_nvr=nvr)

    with source:
        items = list(source)

    vmi_items = [i for i in items if isinstance(i, VMIPushItem)]

    assert len(vmi_items) == 1

    assert isinstance(vmi_items[0], AmiPushItem)
    assert vmi_items == [
        AmiPushItem(
            name="foo-1.0-20230110.sp.22.raw.xz",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/rhel/8.7/1/images/foo-1.0-20230110.sp.22.raw.xz",
            ),
            dest=[],
            md5sum="00000000000000000000000000000000",
            sha256sum=None,
            origin="RHSA-2022:78146",
            build="rhel-ec2-8.7-1",
            build_info=KojiBuildInfo(
                name="rhel",
                version="8.7",
                release="1",
                id="1234",
            ),
            signing_key=None,
            release=AmiRelease(
                product="RHEL",
                date=datetime.date(2022, 12, 20),
                arch="x86_64",
                respin=1,
                version="8.7",
                base_product=None,
                base_version=None,
                variant=None,
                type=None,
            ),
            description="",
            type=None,
            region=None,
            virtualization=None,
            volume=None,
            root_device=None,
            sriov_net_support=None,
            ena_support=None,
            billing_codes=None,
            release_notes=None,
            usage_instructions=None,
            recommended_instance_type=None,
            marketplace_entity_type=None,
            image_id=None,
            public_image=None,
            scanning_port=None,
            user_name=None,
            version_title=None,
            security_groups=[],
        )
    ]


def test_errata_vhd_via_koji(fake_errata_tool, fake_koji, koji_dir):
    """Errata source containing a module yields modules & RPMs taken
    from koji source"""

    source = Source.get(
        "errata:https://errata.example.com",
        errata="RHBA-2022:78522",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    nvr = "rhel-azure-8.7-20221115.sp.1"
    name = "rhel"
    version = "8.7"
    release = "1"

    # Insert some data
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": name,
        "version": version,
        "release": release,
        "nvr": nvr,
        "completion_time": "2022-12-20 12:30:25",
        "extra": {"typeinfo": {"image": {}}},
    }
    fake_koji.build_data[nvr] = fake_koji.build_data[1234]

    imgs = {
        "foo-1.0-20230110.sp.22.vhd.xz": "vhd-compressed",
    }

    archives = []
    for fname, tname in imgs.items():
        archives.append(
            {
                "btype": "image",
                "filename": fname,
                "checksum": "00000000000000000000000000000000",
                "extra": {"image": {"arch": "x86_64"}},
                "type_name": tname,
                "build_id": 1234,
                "nvr": nvr,
            }
        )

    fake_koji.insert_archives(archives=archives, build_nvr=nvr)

    with source:
        items = list(source)

    vmi_items = [i for i in items if isinstance(i, VMIPushItem)]

    assert len(vmi_items) == 1

    assert isinstance(vmi_items[0], VHDPushItem)
    assert vmi_items == [
        VHDPushItem(
            name="foo-1.0-20230110.sp.22.vhd.xz",
            state="PENDING",
            src=os.path.join(
                koji_dir,
                "packages/rhel/8.7/1/images/foo-1.0-20230110.sp.22.vhd.xz",
            ),
            dest=[],
            md5sum="00000000000000000000000000000000",
            sha256sum=None,
            origin="RHBA-2022:78522",
            build="rhel-azure-8.7-20221115.sp.1",
            build_info=KojiBuildInfo(
                name="rhel",
                version="8.7",
                release="1",
                id="1234",
            ),
            signing_key=None,
            release=VMIRelease(
                product="RHEL",
                date=datetime.date(2022, 12, 20),
                arch="x86_64",
                respin=1,
                version="8.7",
                base_product=None,
                base_version=None,
                variant=None,
                type=None,
            ),
            description="",
            generation="V2",
            sku_id=None,
            support_legacy=False,
            legacy_sku_id=None,
            disk_version=None,
            recommended_sizes=[],
            sas_uri=None,
        )
    ]
