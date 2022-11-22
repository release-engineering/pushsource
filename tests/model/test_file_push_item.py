import pytest

from pushsource import FilePushItem


@pytest.mark.parametrize("value", [float("nan"), -1e17, 1e17])
def test_display_order_invalid(value):
    """Verify that ValueError is raised when attempting to set display_order
    to an out of range value."""

    with pytest.raises(ValueError) as excinfo:
        FilePushItem(name="item", display_order=value)
    assert "display_order must be within range -99999 .. 99999" in str(excinfo.value)


def test_no_size():
    "Model without src attribute should have size == None"
    file_push_item = FilePushItem(
        name="some-iso",
        state="PENDING",
        src=None,
        dest=["dest2"],
        md5sum=None,
        sha256sum="db68c8a70f8383de71c107dca5fcfe53b1132186d1a6681d9ee3f4eea724fabb",
        origin=None,
        build=None,
        build_info=None,
        signing_key=None,
        description="My wonderful ISO",
        version=None,
        display_order=None,
    )
    assert file_push_item.size == None
