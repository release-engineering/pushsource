from datetime import datetime

from pytest import raises

from pushsource import VHDPushItem, VMIRelease, AmiRelease


def test_invalid_disk_version():
    """Can't create VHDPushItem with bogus disk version."""
    with raises(ValueError) as exc_info:
        VHDPushItem(
            name="test",
            description="test",
            sas_uri="foo.com/bar",
            disk_version="1.0",
        )

    assert r"Invalid disk version. Expected format: {int}.{int}.{int}" in str(
        exc_info.value
    )


def test_vmi_release():
    """Ensure that subclasses of VMIRelease can not be associated with VHDPushItem."""
    release_params = {
        "product": "myprod",
        "arch": "x86_64",
        "respin": 1,
        "date": datetime.now(),
    }
    release = VMIRelease(**release_params)

    assert VHDPushItem(
        name="test",
        description="test",
        sas_uri="foo.com/bar",
        disk_version="1.0.0",
        release=release,
    )

    release = AmiRelease(**release_params)

    with raises(ValueError) as exc_info:
        VHDPushItem(
            name="test",
            description="test",
            sas_uri="foo.com/bar",
            disk_version="1.0.0",
            release=release,
        )

    assert 'The release type must be "VMIRelease"' in str(exc_info.value)
