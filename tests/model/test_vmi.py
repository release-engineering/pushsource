from pytest import raises

from pushsource import VMIRelease


def test_invalidate_datestr():
    """Can't create an VmiRelease with bogus date string."""
    with raises(ValueError) as exc_info:
        VMIRelease(product="myprod", arch="x86_64", respin=1, date="not-a-real-date")

    assert "can't parse 'not-a-real-date' as a date" in str(exc_info.value)
