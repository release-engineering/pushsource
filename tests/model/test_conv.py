"""Test a few converters on models directly which are difficult to test
otherwise."""

from datetime import datetime

import pytest
from dateutil.tz import tzutc

from pushsource._impl.model.conv import sloppyintlist, timestamp


def test_sloppyintlist_str():
    """sloppyintlist parses comma-separated list of integers."""

    assert sloppyintlist("1,2,3") == [1, 2, 3]


def test_sloppyintlist_ints():
    """sloppyintlist accepts existing lists of integers/strings."""

    assert sloppyintlist([1, "2", 3]) == [1, 2, 3]


def test_sloppyintlist_immutable():
    """sloppyintlist's output is immutable."""

    mylist = sloppyintlist([1, 2, 3])
    with pytest.raises(NotImplementedError):
        mylist.append(4)


def test_sloppyintlist_invalid():
    """sloppyintlist raises if given non-integer strings."""

    with pytest.raises(ValueError):
        sloppyintlist("1,foo,3")


@pytest.mark.parametrize("datestr", ["2020-01-02T03:04:05Z", "2020-01-02T03:04:05"])
def test_timestamp_withsec(datestr):
    """timestamp can parse expected datetime strings (with seconds)"""

    assert timestamp(datestr) == datetime(2020, 1, 2, 3, 4, 5, tzinfo=tzutc())


@pytest.mark.parametrize("datestr", ["2020-01-02T03:04Z", "2020-01-02T03:04"])
def test_timestamp_nosec(datestr):
    """timestamp can parse expected datetime strings (without seconds)"""

    assert timestamp(datestr) == datetime(2020, 1, 2, 3, 4, tzinfo=tzutc())


def test_timestamp_invalid():
    """timestamp raises if given unparseable string"""

    with pytest.raises(ValueError) as exc:
        timestamp("hamburger")

    assert "can't parse 'hamburger' as a timestamp" in str(exc.value)
