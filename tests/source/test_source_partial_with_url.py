"""Test cases mixing get_partial with url arguments."""

import pytest

from pushsource import Source, PushItem


class ReturnsUrlSource(object):
    """A source which yields a push item with the input arguments embedded into
    name, so that we can see what was passed in.
    """

    def __init__(self, url, a="a", b="b"):
        self._url = url
        self._a = a
        self._b = b

    def __iter__(self):
        yield PushItem(name="%s %s %s" % (self._url, self._a, self._b))


@pytest.fixture(autouse=True)
def source_reset():
    """Does Source.reset after every test, since we are messing with
    the registered backends."""
    yield
    Source.reset()


def test_partial_with_url_unbound():
    Source.register_backend("returns-url", ReturnsUrlSource)

    # Let's say that I now overwrite this source with an argument (not url) bound
    partial = Source.get_partial("returns-url:", a=123)
    Source.register_backend("returns-url", partial)

    # Then I should be able to obtain an instance of this source, and it
    # should still stuff the path part of the below string into the 'url' arg
    items = [i for i in Source.get("returns-url:/foo/bar?b=88")]

    assert items == [PushItem(name="/foo/bar 123 88")]


def test_partial_with_url_bound():
    Source.register_backend("returns-url", ReturnsUrlSource)

    # Let's say that I now overwrite this source and I pre-fill a URL
    partial = Source.get_partial("returns-url:", url="/dummy")
    Source.register_backend("returns-url", partial)

    # Then I should be able to obtain an instance of this source, with
    # the URL coming from the value previously bound and other arguments
    # still able to be overridden normally.
    items = [i for i in Source.get("returns-url:b=123")]

    assert items == [PushItem(name="/dummy a 123")]


def test_partial_with_url_bound_overwrite():
    Source.register_backend("returns-url", ReturnsUrlSource)

    # Let's say that I now overwrite this source and I pre-fill a URL
    partial = Source.get_partial("returns-url:", url="/dummy")
    Source.register_backend("returns-url", partial)

    # Then I should be able to obtain an instance of this source, and
    # I can still override the bound URL by passing a new one in the
    # normal manner.
    items = [i for i in Source.get("returns-url:/other/url?a=1&b=2")]

    assert items == [PushItem(name="/other/url 1 2")]
