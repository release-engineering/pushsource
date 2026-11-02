from pytest import raises

from pushsource import PushItem


def test_to_sync_default_false():
    """to_sync defaults to False for an ordinary push item."""
    item = PushItem(name="test")

    assert item.to_sync is False


def test_to_sync_set_true():
    """to_sync can be set to True by a source producing remote content."""
    item = PushItem(name="test", to_sync=True)

    assert item.to_sync is True


def test_to_sync_rejects_non_bool():
    """to_sync only accepts a bool."""
    with raises(TypeError):
        PushItem(name="test", to_sync="yes")
