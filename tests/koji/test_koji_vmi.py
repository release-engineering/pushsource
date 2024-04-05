import os

from pytest import raises, mark

from pushsource import (
    Source,
    AmiPushItem,
    VHDPushItem,
    VMIPushItem,
    BootMode,
    AmiRelease,
    VMIRelease,
    KojiBuildInfo,
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


@mark.parametrize("boot_mode", [None, "legacy", "uefi", "hybrid"])
def test_koji_vmis(boot_mode, fake_koji, koji_dir):
    """Koji source yields requested Virtual Machine Images."""

    name = "foobuild"
    version = "1.0"
    release = "20230110.sp.22"
    nvr = "%s-%s-%s" % (name, version, release)
    boot_mode_enum = BootMode(boot_mode) if boot_mode else None

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
                "extra": {"image": {"arch": "x86_64", "boot_mode": boot_mode}},
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
            boot_mode=boot_mode_enum,
            dest=[],
            description="",
            md5sum="00000000000000000000000000000000",
            sha256sum=None,
            origin=None,
            build=nvr,
            build_info=KojiBuildInfo(
                name=name, version=version, release=release, id=1234
            ),
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
        boot_mode=None,
        dest=[],
        description="",
        md5sum="00000000000000000000000000000000",
        sha256sum=None,
        origin=None,
        build="foobuild-azure-1.0-1",
        build_info=KojiBuildInfo(
            name="foobuild-azure", version="1.0", release="1", id=1234
        ),
        signing_key=None,
        release=rel_obj,
    )


@mark.parametrize("boot_mode", [None, "legacy", "uefi", "hybrid"])
def test_coreos_assembler_image(boot_mode, fake_koji, koji_dir):
    boot_mode_enum = BootMode(boot_mode) if boot_mode else None

    archives = []
    images = {
        "meta.json": "json",
        "commitmeta.json": "json",
        "coreos-assembler-git.tar.gz": "tar",
    }
    for file_name, type_name in images.items():
        archives.append(
            {
                "btype": "image",
                "btype_id": 4,
                "build_id": 123456,
                "buildroot_id": 1234567,
                "checksum": "dde60621880aa996c42e356a687744ef",
                "checksum_type": 0,
                "compression_type": None,
                "filename": file_name,
                "id": 234792,
                "metadata_only": False,
                "size": 16077,
                "type_description": "JSON data",
                "type_extensions": "json",
                "type_id": 49,
                "type_name": type_name,
            }
        )

    name = "rhcos"
    version = "4.11"
    release = "1"
    nvr = f"{name}-{version}-{release}"

    source = Source.get(
        f"koji:https://koji.example.com/?vmi_build={nvr}", basedir=koji_dir
    )
    assert not fake_koji.last_url

    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": name,
        "version": version,
        "release": release,
        "nvr": nvr,
        "completion_time": "2022-12-20 12:30:25",
        "extra": {"typeinfo": {"image": {"arch": "x86_64", "boot_mode": boot_mode}}},
    }

    fake_koji.build_data[nvr] = fake_koji.build_data[1234]

    fake_koji.insert_archives(archives=archives, build_nvr=nvr)

    meta_data_directory = os.path.join(
        koji_dir, "packages", name, version, release, "images"
    )
    os.makedirs(meta_data_directory)
    meta_data_path = os.path.join(meta_data_directory, "meta.json")

    meta_data = """{    
    "name": "rhcos",
    "summary": "OpenShift 4",
    "coreos-assembler.container-config-git":{
            "branch": "release-4.11"
    },
    "images": {
        "azure": {
            "path": "rhcos-4.11-0-azure.x86_64.vhd.gz",
            "sha256": "2cd817331af29093e2eaa025139ebddd6008c193970b06b35afbbdbebae0ce3e",
            "dest": ["https://example.windows.net/imagebucket/rhcos-4.11-0-azure.x86_64.vhd"]},
  "aws": {
        "path": "rhcos-4.11-0-aws.x86_64.vmdk.gz",
        "sha256": "4ef7806152bd89ce44326ff746c4f1883ad543885e980bce59821df2d946ea4c"
        }},
 "azure": {
        "image": "rhcos-4.11-0-azure.x86_64.vhd",
        "url": "https://example.windows.net/imagebucket/rhcos-4.11-0-azure.x86_64.vhd"},
 "amis": [
    {"name": "us-gov-west-1",
   "hvm": "ami-01"
   },
    {"name": "us-east-1",
   "hvm": "ami-02"
   }]}"""

    with open(meta_data_path, "w") as rhcos_metadata:
        rhcos_metadata.write(meta_data)
    items = list(source)

    vms_with_custom_meta_data = [
        {
            "marketplace_name": "aws",
            "push_item_class": AmiPushItem,
            "custom_meta_data": {"region": "us-gov-west-1", "src": "ami-01"},
            "sha256": "4ef7806152bd89ce44326ff746c4f1883ad543885e980bce59821df2d946ea4c",
        },
        {
            "marketplace_name": "aws",
            "push_item_class": AmiPushItem,
            "custom_meta_data": {"region": "us-east-1", "src": "ami-02"},
            "sha256": "4ef7806152bd89ce44326ff746c4f1883ad543885e980bce59821df2d946ea4c",
        },
        {
            "marketplace_name": "azure",
            "push_item_class": VHDPushItem,
            "custom_meta_data": {
                "src": "https://example.windows.net/imagebucket/rhcos-4.11-0-azure.x86_64.vhd"
            },
            "sha256": "2cd817331af29093e2eaa025139ebddd6008c193970b06b35afbbdbebae0ce3e",
        },
    ]

    out = []
    for vm_item in vms_with_custom_meta_data:
        klass = vm_item.get("push_item_class")
        rel_klass = klass._RELEASE_TYPE
        release = rel_klass(
            arch="x86_64",
            date="2022-12-20",
            product="RHCOS",
            version="4.11",
            respin=1,
        )

        out.append(
            klass(
                name="rhcos",
                description="OpenShift 4",
                **vm_item["custom_meta_data"],
                boot_mode=boot_mode_enum,
                build="rhcos-4.11-1",
                build_info=KojiBuildInfo(
                    id=1234,
                    name="rhcos",
                    version="4.11",
                    release="1",
                ),
                sha256sum=vm_item.get("sha256"),
                release=release,
                marketplace_name=vm_item["marketplace_name"],
            )
        )
    items = sorted(items, key=lambda metadata: metadata.name)
    assert items == out
