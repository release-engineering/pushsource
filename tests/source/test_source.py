import copy
from pytest import raises, fixture

from pushsource import Source, SourceUrlError


def test_source_abstract():
    """Source is an abstract base class, can't be iterated over directly."""
    instance = Source()

    with raises(NotImplementedError):
        list(instance)


def test_register_invalid():
    """Registering non-callable Source fails."""
    with raises(TypeError):
        Source.register_backend("foobar", "some wrong value")


def test_args_from_url():
    """Arguments from URLs are passed through to registered Source as expected."""

    calls = []

    def gather_args(*args, **kwargs):
        calls.append((args, kwargs))
        return []

    Source.register_backend("abc", gather_args)

    Source.get("abc:key=val1&key=val2&threads=10&timeout=60&foo=bar,baz")

    # It should have made a call to the registered backend with the given arguments:
    assert len(calls) == 1
    assert calls[0] == (
        (),
        {
            # Repeating key is passed as a list
            "key": ["val1", "val2"],
            # Threads/timeout are converted to int
            "threads": 10,
            "timeout": 60,
            # CSV are not automatically split into a list; Source class itself
            # must handle this if desired
            "foo": "bar,baz",
        },
    )


def test_args_via_partial():
    """Arguments are passed into source via get_partial as expected."""

    calls = []

    def gather_args(*args, **kwargs):
        calls.append((args, kwargs))
        return []

    Source.register_backend("gather", gather_args)

    # Let's make a partial bound to 'a' & 'b' by default
    gather = Source.get_partial("gather:a=1", b=2)

    # Call it a few different ways:
    gather()
    gather(c=3)
    gather(d=4)

    # It should have been called with expected args:
    # - every call had 'a' & 'b' since they were bound in get_partial
    # - 'b' and 'c' only appear when explicitly passed
    # - also note 'a' is a string since it came via URL
    assert len(calls) == 3
    assert calls[0] == ((), {"a": "1", "b": 2})
    assert calls[1] == ((), {"a": "1", "b": 2, "c": 3})
    assert calls[2] == ((), {"a": "1", "b": 2, "d": 4})


def test_bad_url_no_scheme():
    with raises(SourceUrlError) as ex_info:
        Source.get("no-scheme")

    assert "Not a valid source URL: no-scheme" in str(ex_info.value)


def test_bad_url_missing_backend():
    with raises(SourceUrlError) as ex_info:
        Source.get("notexist:foo=bar&baz=quux")

    assert (
        "Requested source 'notexist:foo=bar&baz=quux' but "
        "there is no registered backend 'notexist'"
    ) in str(ex_info.value)
