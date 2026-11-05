import os

from pytest import raises

from pushsource import (
    Source,
    AmiPushItem,
    AmiRelease,
    VHDPushItem,
    VMIRelease,
    KojiBuildInfo,
    BootMode,
)

DATADIR = os.path.join(os.path.dirname(__file__), "data")


def _write_stage(tmpdir, resources_yaml, files=None, dest="starmap", build="build1"):
    cloud = tmpdir.mkdir(dest).mkdir("CLOUD_IMAGES").mkdir(build)
    cloud.join("resources.yaml").write(resources_yaml)
    for name, content in (files or {}).items():
        cloud.join(name).write(content)
    return str(tmpdir)


def test_staged_cloud_copy_and_combined():
    """Remote-only and combined path+remote CLOUD_IMAGES yield copy & upload items."""
    staged_dir = os.path.join(DATADIR, "cloud_copy")
    items = list(Source.get("staged:" + staged_dir))
    items.sort(
        key=lambda item: (type(item).__name__, item.origin or "", item.src, item.name)
    )

    aws_origin = os.path.join(staged_dir, "starmap/CLOUD_IMAGES/rhcos-aws")
    azure_origin = os.path.join(staged_dir, "starmap/CLOUD_IMAGES/rhcos-azure")
    combined_origin = os.path.join(staged_dir, "starmap/CLOUD_IMAGES/combined-aws")
    local_raw = os.path.join(combined_origin, "rhcos-9.6.20251212-1-aws.x86_64.raw")

    release_x86 = AmiRelease(
        product="RHCOS",
        date="20260603",
        arch="x86_64",
        respin=0,
        version="4.21",
    )
    build_info = KojiBuildInfo(name="RHCOS", version="4.21", release="0")

    assert items == [
        AmiPushItem(
            name="rhcos-9.6.20251212-1-aws.x86_64.raw",
            src=local_raw,
            dest=["starmap"],
            origin=combined_origin,
            build_info=build_info,
            description="",
            boot_mode=BootMode.hybrid,
            type="AMI",
            release=release_x86,
        ),
        AmiPushItem(
            name="ami-04018496b0a1da2d2",
            src="ami-04018496b0a1da2d2",
            dest=["starmap"],
            origin=combined_origin,
            build_info=build_info,
            description="",
            boot_mode=BootMode.hybrid,
            type="AMI",
            image_id="ami-04018496b0a1da2d2",
            release=release_x86,
        ),
        AmiPushItem(
            name="ami-04018496b0a1da2d2",
            src="ami-04018496b0a1da2d2",
            dest=["starmap"],
            origin=aws_origin,
            build_info=build_info,
            description="",
            boot_mode=BootMode.hybrid,
            type="AMI",
            image_id="ami-04018496b0a1da2d2",
            release=release_x86,
        ),
        VHDPushItem(
            name="rhcos-9.6.20251212-1-azure.x86_64.vhd",
            src="https://rhcos.blob.core.windows.net/imagebucket/rhcos-9.6.20251212-1-azure.x86_64.vhd",
            dest=["starmap"],
            origin=azure_origin,
            build_info=build_info,
            description="",
            sas_uri="https://rhcos.blob.core.windows.net/imagebucket/rhcos-9.6.20251212-1-azure.x86_64.vhd",
            release=VMIRelease(
                product="RHCOS",
                date="20260603",
                arch="x86_64",
                respin=0,
                version="4.21",
            ),
        ),
    ]


def test_staged_cloud_remote_overrides_image_id(tmpdir):
    """Per-image remote wins over a top-level image_id in resources.yaml."""
    staged = _write_stage(
        tmpdir,
        """
api: v1
resource: CloudImage
images:
  - remote: ami-remotevalue
    architecture: x86_64
build:
  name: RHCOS
  version: "4.21"
  respin: "0"
release:
  date: "20260603"
description: ""
type: AMI
image_id: ami-from-resources
""",
    )

    items = list(Source.get("staged:" + staged))
    assert len(items) == 1
    assert items[0].image_id == "ami-remotevalue"
    assert items[0].src == "ami-remotevalue"


def test_staged_cloud_remote_name_fallback(tmpdir):
    """Remote URIs without a path basename use the full location as the name."""
    staged = _write_stage(
        tmpdir,
        """
api: v1
resource: CloudImage
images:
  - remote: "https://storage.example.com/"
    architecture: x86_64
build:
  name: RHCOS
  version: "4.21"
  respin: "0"
release:
  date: "20260603"
description: ""
type: VHD
""",
    )

    items = list(Source.get("staged:" + staged))
    assert len(items) == 1
    assert items[0].name == "https://storage.example.com/"
    assert items[0].src == "https://storage.example.com/"
    assert items[0].sas_uri == "https://storage.example.com/"


def test_staged_cloud_remote_name_strips_query_string(tmpdir):
    """A remote URL's query string (e.g. a SAS token) is not included in the derived name."""
    staged = _write_stage(
        tmpdir,
        """
api: v1
resource: CloudImage
images:
  - remote: "https://storage.example.com/dir/file.vhd?sv=2020-01-01&sig=abc123"
    architecture: x86_64
build:
  name: RHCOS
  version: "4.21"
  respin: "0"
release:
  date: "20260603"
description: ""
type: VHD
""",
    )

    items = list(Source.get("staged:" + staged))
    assert len(items) == 1
    assert items[0].name == "file.vhd"
    assert (
        items[0].src
        == "https://storage.example.com/dir/file.vhd?sv=2020-01-01&sig=abc123"
    )
    assert (
        items[0].sas_uri
        == "https://storage.example.com/dir/file.vhd?sv=2020-01-01&sig=abc123"
    )


def test_staged_cloud_path_and_remote_mutex(tmpdir):
    """Setting both path and remote on one image is an error."""
    staged = _write_stage(
        tmpdir,
        """
api: v1
resource: CloudImage
images:
  - path: local.raw
    remote: ami-04018496b0a1da2d2
    architecture: x86_64
build:
  name: RHCOS
  version: "4.21"
  respin: "0"
release:
  date: "20260603"
description: ""
type: AMI
""",
        files={"local.raw": ""},
    )

    with raises(ValueError) as exc_info:
        list(Source.get("staged:" + staged))

    assert "must not set both 'path' and 'remote'" in str(exc_info.value)


def test_staged_cloud_missing_path_and_remote(tmpdir):
    """An image with neither path nor remote is an error."""
    staged = _write_stage(
        tmpdir,
        """
api: v1
resource: CloudImage
images:
  - architecture: x86_64
build:
  name: RHCOS
  version: "4.21"
  respin: "0"
release:
  date: "20260603"
description: ""
type: AMI
""",
    )

    with raises(ValueError) as exc_info:
        list(Source.get("staged:" + staged))

    assert "must set exactly one of 'path' or 'remote'" in str(exc_info.value)
