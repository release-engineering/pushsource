from pushsource._impl.helpers import list_argument


def test_list_argument():
    assert list_argument(None) == []
    assert list_argument("") == []
    assert list_argument(123) == [123]
    assert list_argument("123") == ["123"]
    assert list_argument("123,456,789") == ["123", "456", "789"]
