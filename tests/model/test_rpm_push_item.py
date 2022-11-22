from pushsource import Source, RpmPushItem


def test_rpm_empty_file_size(caplog):
    rpm_push_item = RpmPushItem(
        name="walrus-5.21-1.noarch.rpm",
        state="PENDING",
        src=None,
        dest=["dest1"],
        md5sum=None,
        sha256sum=None,
        origin=None,
        build=None,
        # Note this signing key was extracted from RPM headers.
        signing_key="F78FB195",
    )
    assert rpm_push_item.size == None
