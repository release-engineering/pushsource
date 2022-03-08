# Converters and validators for use with model classes.
import datetime
import logging
from functools import partial
import re

import six
from frozenlist2 import frozenlist
from dateutil import tz

from .. import compat_attr as attr


LOG = logging.getLogger("pushsource")
HEX_PATTERN = re.compile(r"^[0-9a-f]+$")

# Work around http://bugs.python.org/issue7980 which is closed "Won't Fix"
# for python2:
#
# If multiple threads in a process do the first call to strptime at once,
# a crash can occur. Calling strptime once at import time will avoid that
# condition.
#
# TODO: remove me when py2 support is dropped
datetime.datetime.strptime("", "")


def sloppylist(value, elem_converter=None):
    """Accept real lists or comma-separated values, and output a frozen list.

    Optionally use elem_converter to convert each list element.
    """
    if isinstance(value, six.string_types):
        value = value.split(",")
    if elem_converter:
        value = [elem_converter(elem) for elem in value]
    return frozenlist(value)


sloppyintlist = partial(sloppylist, elem_converter=int)


def timestamp(value):
    if isinstance(value, six.string_types):
        for fmt in (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%MZ",
            "%Y-%m-%dT%H:%M",
        ):
            try:
                value = datetime.datetime.strptime(value, fmt)
                break
            except ValueError:
                LOG.debug("can't parse %s using %s", value, fmt, exc_info=1)
        else:
            raise ValueError("can't parse %s as a timestamp" % repr(value))

    # If it's not timezone-aware, force UTC
    if not value.tzinfo:
        value = value.replace(tzinfo=tz.tzutc())

    return value


def datestr(value):
    if isinstance(value, six.string_types):
        for fmt in ("%Y%m%d", "%Y-%m-%d"):
            try:
                value = datetime.datetime.strptime(value, fmt)
                value = datetime.date(value.year, value.month, value.day)
                break
            except ValueError:
                LOG.debug("can't parse %s using %s", value, fmt, exc_info=1)
        else:
            raise ValueError("can't parse %s as a date" % repr(value))

    return value


def hexstr(length, value):
    if value is None:
        return value

    msg = "can't parse %s as a hex string" % repr(value)

    if not isinstance(value, six.string_types):
        raise TypeError(msg)

    if len(value) != length:
        raise ValueError("wrong length of %s (expected: %s)" % (repr(value), length))

    value = value.lower()
    if not HEX_PATTERN.match(value):
        raise ValueError(msg)

    return value


md5str = partial(hexstr, 32)
sha1str = partial(hexstr, 40)
sha256str = partial(hexstr, 64)


def archstr(value):
    """Convert a handful of arch aliases into canonical form for consistent comparisons."""
    if value == "amd64":
        return "x86_64"
    if value == "SRPM":
        return "src"
    return value


def upper_if_str(value):
    if isinstance(value, six.string_types):
        return value.upper()
    return value


def int2str(value):
    # If value is an integer, convert it to string instead.
    # Mostly used for "numeric string" fields on errata, such as pushcount.
    if isinstance(value, int):
        return str(value)
    return value


def convert_maybe(fn):
    # Given a conversion function, returns a wrapped function which performs
    # no conversion on None values.
    #
    # This is useful for the common case of an optional attribute (default=None),
    # where a converter should be applied if and only if the default value isn't
    # being used.

    def out(value):
        if value is None:
            return None
        return fn(value)

    return out


in_ = attr.validators.in_
instance_of = attr.validators.instance_of
instance_of_str = instance_of(six.string_types)
optional = attr.validators.optional
optional_str = optional(instance_of_str)
