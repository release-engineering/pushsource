import pytest

from pushsource._impl.helpers import list_argument, try_bool, force_https


def test_list_argument():
    assert list_argument(None) == []
    assert list_argument("") == []
    assert list_argument(123) == [123]
    assert list_argument("123") == ["123"]
    assert list_argument("123,456,789") == ["123", "456", "789"]


@pytest.mark.parametrize(
    "input,expected_output",
    [
        (True, True),
        (False, False),
        (12345, 12345),
        ("1", True),
        ("true", True),
        ("tRUe", True),
        ("yes", True),
        ("0", False),
        ("false", False),
        ("FaLsE", False),
        ("no", False),
        ("", False),
    ],
)
def test_try_bool(input, expected_output):
    assert try_bool(input) == expected_output


def test_try_bool_invalid():
    with pytest.raises(ValueError):
        try_bool("this ain't no boolean")


@pytest.mark.parametrize(
    "input, expected_output",
    [
        ("http://errata.example.com/some/path", "https://errata.example.com/some/path"),
        (
            "https://errata.example.com/some/path",
            "https://errata.example.com/some/path",
        ),
        (
            "https://errata.example.com/some/path?param1=a",
            "https://errata.example.com/some/path?param1=a",
        ),
        (
            "https://errata.example.com/some/path#fragment",
            "https://errata.example.com/some/path#fragment",
        ),
        (
            "https://errata.example.com/some/path?param1=a#fragment",
            "https://errata.example.com/some/path?param1=a#fragment",
        ),
    ],
)
def test_force_https(input, expected_output):
    assert force_https(input) == expected_output
