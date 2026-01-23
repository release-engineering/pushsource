import os

from pushsource import Source, RpmPushItem

DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_rpm(caplog):
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should find the staged RPMs
    assert files == [
        RpmPushItem(
            name="walrus-5.21-1.noarch.rpm",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/RPMS/walrus-5.21-1.noarch.rpm"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            # Note this signing key was extracted from RPM headers.
            signing_key="F78FB195",
        ),
        RpmPushItem(
            name="test-srpm01-1.0-1.src.rpm",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/SRPMS/test-srpm01-1.0-1.src.rpm"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
        ),
    ]
    # RPM content is read from the source in the push items
    assert files[0].content().name == os.path.join(
        staged_dir, "dest1/RPMS/walrus-5.21-1.noarch.rpm"
    )
    assert files[1].content().name == os.path.join(
        staged_dir, "dest1/SRPMS/test-srpm01-1.0-1.src.rpm"
    )
    # It should also warn about this
    nonrpm_path = os.path.join(staged_dir, "dest1/RPMS/not-an-rpm.txt")
    msg = "Unexpected non-RPM %s (ignored)" % nonrpm_path
    assert msg in caplog.messages
