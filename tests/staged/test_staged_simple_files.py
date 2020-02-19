import os

from pushsource import Source, FilePushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_files():
    staged_dir = os.path.join(DATADIR, "simple_files")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        FilePushItem(
            name="test.txt",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/ISOS/test.txt"),
            dest=["dest1"],
            md5sum=None,
            sha256sum="d8301c5f72f16455dbc300f3d1bef8972424255caad103cc6c7ba7dc92d90ca8",
            origin="staged",
            build=None,
            signing_key=None,
            description=None,
        ),
        FilePushItem(
            name="some-file.txt",
            state="PENDING",
            src=os.path.join(staged_dir, "dest2/FILES/some-file"),
            dest=["dest2"],
            md5sum=None,
            sha256sum="315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3",
            origin="staged",
            build=None,
            signing_key=None,
            description=None,
        ),
        FilePushItem(
            name="some-iso",
            state="PENDING",
            src=os.path.join(staged_dir, "dest2/ISOS/some-iso"),
            dest=["dest2"],
            md5sum=None,
            sha256sum="db68c8a70f8383de71c107dca5fcfe53b1132186d1a6681d9ee3f4eea724fabb",
            origin="staged",
            build=None,
            signing_key=None,
            description="My wonderful ISO",
        ),
    ]
