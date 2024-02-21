from pytest import raises

from pushsource import VMIRelease, VMIPushItem


def test_invalidate_datestr():
    """Can't create an VmiRelease with bogus date string."""
    with raises(ValueError) as exc_info:
        VMIRelease(product="myprod", arch="x86_64", respin=1, date="not-a-real-date")

    assert "can't parse 'not-a-real-date' as a date" in str(exc_info.value)


def test_marketplace_title():
    """Ensure the marketplace_title is properly formed from the template."""

    release = VMIRelease(
        product="myprod", arch="x86_64", version="7.0", respin=1, date="20240101"
    )

    # Template provided
    template = r"Test {product} {arch} {version} - success"
    pi = VMIPushItem(
        description="mydescription",
        name="myname",
        marketplace_title_template=template,
        release=release,
    )
    assert pi.marketplace_title == "Test myprod x86_64 7.0 - success"

    # No template provided
    pi = VMIPushItem(
        description="mydescription",
        name="myname",
        release=release,
    )
    assert pi.marketplace_title == ""

    # No release provided
    pi = VMIPushItem(
        description="mydescription",
        name="myname",
    )
    assert pi.marketplace_title == ""
