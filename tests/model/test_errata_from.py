"""Tests for special handling of "from" field on errata."""
from pytest import raises
import attr

from pushsource import ErratumPushItem


def test_construct_underscore():
    """Constructing item with 'from_' works correctly."""
    item = ErratumPushItem(name="TEST-123", from_="test-from")

    # Should be identical under both names
    assert item.from_ == "test-from"
    assert getattr(item, "from") == "test-from"


def test_construct_nounderscore():
    """Constructing item with 'from' works correctly."""
    kwargs = {"from": "test-from"}
    item = ErratumPushItem(name="TEST-123", **kwargs)

    # Should be identical under both names
    assert item.from_ == "test-from"
    assert getattr(item, "from") == "test-from"


def test_construct_mixed():
    """Constructing item with both 'from' and 'from_' works correctly,
    with 'from' being preferred."""
    kwargs = {"from": "from1", "from_": "from2"}
    item = ErratumPushItem(name="TEST-123", **kwargs)

    # Should be identical under both names - 'from_' is just discarded
    assert item.from_ == "from1"
    assert getattr(item, "from") == "from1"


def test_evolve_nounderscore():
    """Evolving item with "from" works correctly."""
    kwargs = {"from": "test-from"}
    item = ErratumPushItem(name="TEST-123")
    item = attr.evolve(item, **kwargs)

    # Should be identical under both names
    assert item.from_ == "test-from"
    assert getattr(item, "from") == "test-from"


def test_evolve_underscore():
    """Evolving item with "from_" works correctly."""
    item = ErratumPushItem(name="TEST-123")
    item = attr.evolve(item, from_="test-from")

    # Should be identical under both names
    assert item.from_ == "test-from"
    assert getattr(item, "from") == "test-from"


def test_fields():
    """Item class has "from" field and not "from_" field."""
    fields = attr.fields(ErratumPushItem)

    # It should have a field named "from" with correct name.
    assert hasattr(fields, "from")
    assert getattr(fields, "from").name == "from"

    # It should not have any "from_" field (as this is considered
    # merely an alias, not a proper field).
    assert not hasattr(fields, "from_")

    # Other unrelated fields should work as normal.
    assert hasattr(fields, "status")
    assert fields.status.name == "status"


def test_asdict():
    """asdict() returns "from" and not "from_"."""
    kwargs = {"name": "adv", "from": "bob"}
    item = ErratumPushItem(**kwargs)

    item_dict = attr.asdict(item)

    # It should have exactly the fields from the inputs
    assert item_dict["name"] == kwargs["name"]
    assert item_dict["from"] == kwargs["from"]

    # And it should not have any extra 'from_'
    assert "from_" not in item_dict
