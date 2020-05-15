import os

from pushsource import Source, ProductIdPushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_productid():
    staged_dir = os.path.join(DATADIR, "simple_productid")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        ProductIdPushItem(
            name="some-cert",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/PRODUCTID/some-cert"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
        )
    ]
