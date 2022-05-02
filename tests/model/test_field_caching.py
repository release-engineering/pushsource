from pushsource import PushItem


def test_fields_cached():
    # Try making two items with similar fields.
    # Note: the weird string construction here is meant to defeat
    # the built-in python logic of interning string literals since
    # that would defeat the purpose of the test...
    item1 = PushItem(
        name="item1", origin="some-origin", dest=["a", "b", "c"], signing_key="a1b2c3d4"
    )
    item2 = PushItem(
        name="item2",
        origin="-".join(["some", "origin"]),
        dest=["a", "b", "c"],
        signing_key="2".join(["a1b", "c3d4"]),
    )

    # Field values should be not only equal...
    for item in (item1, item2):
        assert item.origin == "some-origin"
        assert item.dest == ["a", "b", "c"]
        assert item.signing_key == "A1B2C3D4"

    # ...but they should also be *identical*
    assert item1.origin is item2.origin
    assert item1.dest is item2.dest
    assert item1.signing_key is item2.signing_key
