import os
from pytest import raises

from io import UnsupportedOperation

from pushsource import PushItem
from pushsource._impl.utils.openers import open_src_local

ITEM_SRC = os.path.join(os.path.dirname(__file__), "data/test_file.txt")


def test_push_item_content():
    """Read pushitem content from the source"""
    item = PushItem(name="test", src=ITEM_SRC, opener=open_src_local)

    assert item.content().name == ITEM_SRC
    assert item.content().read().decode("utf-8") == "test content\n"
    # content file object should not seekable or wriateble
    assert item.content().seekable() == False
    assert item.content().writable() == False


def test_push_item_seek_fail():
    """Fail when trying to seek content"""
    with raises(UnsupportedOperation) as exc_info:
        item = PushItem(name="test", src=ITEM_SRC, opener=open_src_local)
        item.content().seek(0)

    assert "Seek unsupported" in str(exc_info.value)


def test_push_item_content_without_opener():
    """No content is returned without an opener"""
    item = PushItem(name="test", src=ITEM_SRC)

    assert item.content() == None


def test_push_item_content_context_mgr():
    """Read pushitem content using its context manager"""
    item = PushItem(name="test", src=ITEM_SRC, opener=open_src_local)

    with item.content() as f:
        assert f.name == ITEM_SRC
        assert f.read().decode("utf-8") == "test content\n"
