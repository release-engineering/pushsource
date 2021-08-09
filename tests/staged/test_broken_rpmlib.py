import pytest

from pushsource._impl.backend import broken_rpmlib


@pytest.mark.parametrize(
    "fn", [broken_rpmlib.get_keys_from_header, broken_rpmlib.get_rpm_header]
)
def test_functions_raise(fn):
    """Expected functions are present in broken_rpmlib and raise on use."""

    with pytest.raises(RuntimeError) as excinfo:
        fn("a", "b", "c")

    assert "kobo.rpmlib is not available" in str(excinfo)
