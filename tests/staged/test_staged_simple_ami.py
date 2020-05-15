import os

from pushsource import Source, AmiPushItem, AmiRelease


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_ami():
    staged_dir = os.path.join(DATADIR, "simple_ami")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        AmiPushItem(
            name="fake-image.raw",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/AWS_IMAGES/fake-image.raw"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
            release=AmiRelease(
                product="Fake-Product",
                date="20200511",
                arch="x86_64",
                respin=1,
                version="Fake-Version",
                base_product=None,
                base_version=None,
                variant="Fake-Variant",
                type="ga",
            ),
            type="access",
            region="cn-north-1",
            virtualization="hvm",
            volume="gp2",
            root_device="/dev/sda1",
            description="A sample image for testing",
            sriov_net_support="simple",
            ena_support=True,
        )
    ]
