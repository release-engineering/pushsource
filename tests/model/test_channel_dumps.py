from pytest import raises

from pushsource import ChannelDumpPushItem


def test_invalidate_datetime():
    """Can't create a ChannelDumpPushItem with an invalid datetime."""
    with raises(ValueError) as exc_info:
        ChannelDumpPushItem(name="somefile", datetime="not a valid timestamp")

    assert "can't parse 'not a valid timestamp' as a timestamp" in str(exc_info.value)
