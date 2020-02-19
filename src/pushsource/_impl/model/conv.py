# Converters and validators for use with model classes.
import datetime
import logging
from functools import partial

import six
from frozenlist2 import frozenlist
from dateutil import tz


LOG = logging.getLogger("pushsource")


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
