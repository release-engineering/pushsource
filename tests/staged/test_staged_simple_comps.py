import os

from pushsource import Source, CompsXmlPushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_comps():
    staged_dir = os.path.join(DATADIR, "simple_comps")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        CompsXmlPushItem(
            name="rawhide-everything.xml",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/COMPS/rawhide-everything.xml"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
        )
    ]
