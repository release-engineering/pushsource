from datetime import datetime

from pytest import raises

from pushsource import AmiRelease, AmiPushItem, VMIRelease


def test_invalidate_datestr():
    """Can't create an AmiRelease with bogus date string."""
    with raises(ValueError) as exc_info:
        AmiRelease(product="myprod", arch="x86_64", respin=1, date="not-a-real-date")

    assert "can't parse 'not-a-real-date' as a date" in str(exc_info.value)


def test_ami_release():
    """Ensure that AmiRelease can only be associated with AmiPushItem."""
    release_params = {
        "product": "myprod",
        "arch": "x86_64",
        "respin": 1,
        "date": datetime.now(),
    }
    release = AmiRelease(**release_params)

    assert AmiPushItem(
        description="mydescription",
        name="myname",
        region="myregion",
        root_device="myrootdevice",
        virtualization="virt",
        volume="myvolume",
        release=release,
        sriov_net_support="sriov",
    )

    release = VMIRelease(**release_params)

    with raises(ValueError) as exc_info:
        AmiPushItem(
            description="mydescription",
            name="myname",
            release=release,
        )

    assert 'The release type must be "AmiRelease"' in str(exc_info.value)
