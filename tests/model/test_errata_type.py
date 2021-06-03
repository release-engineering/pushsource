import pytest

from pushsource import ErratumPushItem


@pytest.mark.parametrize(
    "in_type,out_type",
    [
        ("RHBA", "bugfix"),
        ("RHEA", "enhancement"),
        ("RHSA", "security"),
        ("bugfix", "bugfix"),
        ("enhancement", "enhancement"),
        ("security", "security"),
    ],
)
def test_type_converted(in_type, out_type):
    """ErratumPushItem converts values of 'type' field to one of the expected."""
    item = ErratumPushItem(name="TEST-123", type=in_type)
    assert item.type == out_type


def test_type_enforced():
    """ErratumPushItem complains on invalid values for 'type'"""
    with pytest.raises(ValueError):
        ErratumPushItem(name="TEST-123", type="oops-bad-type")
