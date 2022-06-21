import copy
from pytest import raises, fixture
from mock import patch

from pushsource import Source, SourceUrlError


@fixture
def source_factory(fake_errata_tool, fake_koji, koji_dir):
    ctor = Source.get_partial(
        "errata:https://errata.example.com",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    fake_koji.load_all_builds()

    yield ctor


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


@patch("pushsource._impl.source.time.sleep")
@patch("pushsource._impl.source.os.path.exists")
def test_yield_no_source(mock_path_exists, mock_sleep, source_factory, koji_dir):
    class TestKoji(object):
        def __init__(self, **kwargs):
            self.koji = Source.get("koji:https://koji.example.com?basedir=%s" % koji_dir, **kwargs)

        def __iter__(self):
            class Object:
                pass

            item1 = Object()
            item1.src = None
            yield item1
            yield Object()

    Source.register_backend("test-koji", TestKoji)
    source = source_factory(errata="RHBA-2020:2807", koji_source="test-koji:")
    items = list(source)

    mock_path_exists.assert_not_called()
    mock_sleep.assert_not_called()


@patch("pushsource._impl.source.time.sleep")
@patch("pushsource._impl.source.os.path.exists")
def test_yield_once_file_present(mock_path_exists, mock_sleep, source_factory, koji_dir):
    class TestKoji(object):
        def __init__(self, **kwargs):
            self.koji = Source.get("koji:https://koji.example.com?basedir=%s" % koji_dir, **kwargs)

        def __iter__(self):
            items = list(self.koji)
            yield items[0]

    mock_path_exists.side_effect = [False, False, False, True]
    Source.register_backend("test-koji", TestKoji)
    source = source_factory(errata="RHBA-2020:2807", koji_source="test-koji:")
    items = list(source)

    assert mock_path_exists.call_count == 4
    assert mock_sleep.call_count == 3


@patch("pushsource._impl.source.time.sleep")
@patch("pushsource._impl.source.os.path.exists")
def test_yield_timeout_reached(mock_path_exists, mock_sleep, source_factory, koji_dir):
    class TestKoji(object):
        def __init__(self, **kwargs):
            self.koji = Source.get("koji:https://koji.example.com?basedir=%s" % koji_dir, **kwargs)

        def __iter__(self):
            items = list(self.koji)
            yield items[0]

    mock_path_exists.return_value = False
    Source.register_backend("test-koji", TestKoji)
    source = source_factory(errata="RHBA-2020:2807", koji_source="test-koji:")
    with raises(RuntimeError, match="Push item source .* is missing"):
        items = list(source)

    assert mock_path_exists.call_count == 30
    assert mock_sleep.call_count == 29
