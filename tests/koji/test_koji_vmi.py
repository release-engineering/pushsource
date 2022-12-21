import os

from pytest import raises

from pushsource import (
    Source,
    AmiPushItem,
    VHDPushItem,
    VMIPushItem,
    AmiRelease,
    VMIRelease,
)


def test_koji_vmi_notfound(fake_koji):
    """koji source referencing nonexistent VMI build will fail."""

    source = Source.get("koji:https://koji.example.com/?vmi_build=notexist-1.2.3")
    with raises(ValueError) as exc_info:
        list(source)

    assert "Virtual machine image build not found in koji: notexist-1.2.3" in str(
        exc_info.value
    )


def test_koji_not_vmi_invalid(fake_koji, koji_dir):
    """Koji source referencing an invalid build will fail."""

    source = Source.get(
        "koji:https://koji.example.com/?vmi_build=foobuild-1.0-1", basedir=koji_dir
    )

    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild",
        "version": "1.0",
        "release": "1",
        "nvr": "foobuild-1.0-1",
        "completion_time": "2022-12-20 12:30:25",
    }
    fake_koji.build_data["foobuild-1.0-1"] = fake_koji.build_data[1234]

    with raises(ValueError) as exc_info:
        list(source)

    assert (
        "Build foobuild-1.0-1 not recognized as a virtual machine image build"
        in str(exc_info.value)
    )


def test_koji_not_vmi_container(fake_koji, koji_dir):
    """Koji source referencing a container will fail."""

    source = Source.get(
        "koji:https://koji.example.com/?vmi_build=foobuild-1.0-1", basedir=koji_dir
    )

    # Container image build
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild",
        "version": "1.0",
        "release": "1",
        "nvr": "foobuild-1.0-1",
        "completion_time": "2022-12-20 12:30:25",
        "extra": {"typeinfo": {"image": {}}, "container_koji_task_id": "container"},
    }
    fake_koji.build_data["foobuild-1.0-1"] = fake_koji.build_data[1234]
    with raises(ValueError) as exc_info:
        list(source)

    assert "The build foobuild-1.0-1 is for container images." in str(exc_info.value)


def test_koji_vmis(fake_koji, koji_dir):
    """Koji source yields requested Virtual Machine Images."""

    name = "foobuild"
    version = "1.0"
    release = "20230110.sp.22"
    nvr = "%s-%s-%s" % (name, version, release)

    source = Source.get(
        "koji:https://koji.example.com/?vmi_build=%s" % nvr, basedir=koji_dir
    )

    # It should not have done anything yet (lazy loading)
    assert not fake_koji.last_url

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
        "foo-1.0-20230110.sp.22.img": "generic",
        "foo-1.0-20230110.sp.22.raw.xz": "raw-xz",
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

    # Eagerly fetch
    items = list(source)

    # It should have returned only valid push items for the modules
    assert len(items) == 2

    items = sorted(items, key=lambda pi: pi.name)

    klasses = [AmiPushItem, VHDPushItem]
    index = 0
    imgs.pop("foo-1.0-20230110.sp.22.img")  # Invalid image filtered out by KojiSource

    for klass in klasses:
        fname = sorted(list(imgs.keys()))[index]

        rel_klass = AmiRelease if klass == AmiPushItem else VMIRelease

        rel_obj = rel_klass(
            arch="x86_64",
            date="2022-12-20",
            product="FOOBUILD",
            version=version,
            respin=0,
        )

        assert items[index] == klass(
            name=fname,
            state="PENDING",
            src=os.path.join(
                koji_dir, "packages/foobuild/1.0/20230110.sp.22/images/%s" % fname
            ),
            dest=[],
            description="",
            md5sum="00000000000000000000000000000000",
            sha256sum=None,
            origin=None,
            build=nvr,
            signing_key=None,
            release=rel_obj,
        )
        index += 1


def test_koji_vmi_compound_product_name(fake_koji, koji_dir):
    source = Source.get(
        "koji:https://koji.example.com/?vmi_build=foobuild-azure-1.0-1",
        basedir=koji_dir,
    )

    # Insert some data
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild-azure",
        "version": "1.0",
        "release": "1",
        "nvr": "foobuild-azure-1.0-1",
        "completion_time": "2022-12-20 12:30:25",
        "extra": {"typeinfo": {"image": {}}},
    }
    fake_koji.build_data["foobuild-azure-1.0-1"] = fake_koji.build_data[1234]

    fake_koji.insert_archives(
        archives=[
            {
                "btype": "image",
                "filename": "foo-azure-1.0-1.raw.xz",
                "checksum": "00000000000000000000000000000000",
                "extra": {"image": {"arch": "x86_64"}},
                "type_name": "raw-xz",
                "build_id": 1234,
                "nvr": "foobuild-azure-1.0-1",
            }
        ],
        build_nvr="foobuild-azure-1.0-1",
    )

    # Eagerly fetch
    items = list(source)

    # For product the name "foobuild-azure" should become only "foobuild" in uppercase
    rel_obj = AmiRelease(
        arch="x86_64",
        date="2022-12-20",
        product="FOOBUILD",
        version="1.0",
        respin=1,
    )

    assert items[0] == AmiPushItem(
        name="foo-azure-1.0-1.raw.xz",
        state="PENDING",
        src=os.path.join(
            koji_dir, "packages/foobuild-azure/1.0/1/images/foo-azure-1.0-1.raw.xz"
        ),
        dest=[],
        description="",
        md5sum="00000000000000000000000000000000",
        sha256sum=None,
        origin=None,
        build="foobuild-azure-1.0-1",
        signing_key=None,
        release=rel_obj,
    )
