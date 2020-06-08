from pytest import raises

from pushsource import PushItem


def test_sum_not_string():
    """Can't supply non-string in checksum fields."""

    with raises(TypeError) as exc_info:
        PushItem(name="item", md5sum=1234)
    assert "can't parse 1234 as a hex string" in str(exc_info.value)


def test_sum_incomplete():
    """Can't supply truncated value in checksum fields."""
    with raises(ValueError) as exc_info:
        PushItem(name="item", sha256sum="1234abc")
    assert "wrong length" in str(exc_info.value)


def test_sum_bad_chars():
    """Can't supply non hex strings in checksum fields."""
    with raises(ValueError) as exc_info:
        PushItem(name="item", md5sum="fake7384d113edec49eaa6238ad5ff00")
    assert "can't parse" in str(exc_info.value)


def test_sum_lower():
    """Valid sums are converted to lowercase."""
    item = PushItem(name="item", md5sum="D3B07384D113EDEC49EAA6238AD5FF00")
    assert item.md5sum == "d3b07384d113edec49eaa6238ad5ff00"
