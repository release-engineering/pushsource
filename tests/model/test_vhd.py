from datetime import datetime

from pytest import mark, raises

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


def test_invalid_legacy_sku():
    """Can't create VHDPushItem with legacy_sku set when legacy_support is False."""
    with raises(ValueError) as exc_info:
        VHDPushItem(
            name="test",
            description="test",
            disk_version="1.0.0",
            sas_uri="foo.com/bar",
            support_legacy=False,
            legacy_sku_id="legacy_sku_id",
        )
    assert (
        'The attribute "legacy_sku_id" must only be set when "support_legacy" is True.'
    ) in str(exc_info.value)


@mark.parametrize("value", [True, False, None])
def test_support_legacy(value):
    """Ensure ``support_legacy`` works for all expected inputs."""
    v = VHDPushItem._from_data(
        {
            "name": "test",
            "release": {
                "product": "TEST",
                "date": "20250730",
                "arch": "x86_64",
                "respin": 0,
            },
            "description": "test",
            "disk_version": "1.0.0",
            "sas_uri": "foo.com/bar",
            "support_legacy": value,
        }
    )
    if value:
        assert v.support_legacy == value
    else:
        assert v.support_legacy == False


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
