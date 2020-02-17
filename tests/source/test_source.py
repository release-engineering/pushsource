import copy
from pytest import raises, fixture

from pushsource import Source


@fixture(autouse=True)
def clean_backends():
    """Reset any modifications of Source._BACKENDS performed during tests."""
    backends = copy.deepcopy(Source._BACKENDS)
    yield
    Source._BACKENDS = backends


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
