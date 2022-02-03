import pytest

from pushsource import FilePushItem


@pytest.mark.parametrize("value", [float("nan"), -1e17, 1e17])
def test_display_order_invalid(value):
    """Verify that ValueError is raised when attempting to set display_order
    to an out of range value."""

    with pytest.raises(ValueError) as excinfo:
        FilePushItem(name="item", display_order=value)
    assert "display_order must be within range -99999 .. 99999" in str(excinfo.value)
