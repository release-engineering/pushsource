import os

from pushsource import Source, ModuleMdPushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_modulemd():
    staged_dir = os.path.join(DATADIR, "simple_modulemd")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should load all the expected files with fields filled in by metadata
    assert files == [
        ModuleMdPushItem(
            name="some-modules.yaml",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/MODULEMD/some-modules.yaml"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
        )
    ]
