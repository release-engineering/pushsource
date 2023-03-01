# Converters and validators for use with model classes.
import datetime
import logging
from functools import partial
import re

from frozenlist2 import frozenlist
from frozendict.core import frozendict  # pylint: disable=no-name-in-module
from dateutil import tz

from .. import compat_attr as attr


LOG = logging.getLogger("pushsource")
HEX_PATTERN = re.compile(r"^[0-9a-f]+$")


def sloppylist(value, elem_converter=None):
    """Accept real lists or comma-separated values, and output a frozen list.

    Optionally use elem_converter to convert each list element.
    """
    if isinstance(value, str):
        value = value.split(",")
    if elem_converter:
        value = [elem_converter(elem) for elem in value]
    return frozenlist(value)


sloppyintlist = partial(sloppylist, elem_converter=int)


def timestamp(value):
    if isinstance(value, str):
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
    if isinstance(value, str):
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

    if not isinstance(value, str):
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
    if isinstance(value, str):
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


def freeze(obj):
    """Convert complex object composed of dicts and lists to equivalent object composed of
    frozendicts and frozenlists.
    """

    ret = [None]
    stack = [(obj, ret, 0)]
    traversal = []

    # interate over the structure and do post-order traversal
    while stack:
        cobj, cparent, ckey = stack.pop(0)
        if isinstance(cobj, list):
            for n, i in enumerate(cobj):
                stack.insert(0, (i, cobj, n))
        elif isinstance(cobj, dict):
            for key in cobj:
                stack.insert(0, (cobj[key], cobj, key))
        traversal.insert(0, (cobj, cparent, ckey))

    # Walk through traversal record. As traversal is post-order
    # leafs are processed first and therefore nested dict/lists
    # are replaced froze first
    for titem in traversal:
        cobj, cparent, ckey = titem
        # if traversal entry is list replace it with frozenlist
        if isinstance(cobj, list):
            cparent[ckey] = frozenlist(cobj)
        # if traversal entry is list replace it with frozendict
        elif isinstance(cobj, dict):
            cparent[ckey] = frozendict(cobj)
        else:
            cparent[ckey] = cobj

    return ret[0]


def unfreeze(obj):
    """Convert complex object composed of frozendicts and frozenlists to equivalent object composed of
    dicts and lists.
    """

    ret = [None]
    stack = [(obj, ret, 0)]
    traversal = []

    while stack:
        cobj, cparent, ckey = stack.pop(0)
        # cobj_replacement represents unfrozen object. As structure is processed
        # in post order - leaves are processed first - then it's not possible to
        # assign proccessed leaf to frozen parent.
        # To fix that replace parent object with expected unfrozen object
        cobj_replacement = cobj
        if isinstance(cobj, frozenlist):
            cobj_replacement = [None] * len(cobj)
            for n, i in enumerate(cobj):
                stack.insert(0, (i, cobj_replacement, n))
        elif isinstance(cobj, frozendict):
            cobj_replacement = {}
            for key in cobj:
                stack.insert(0, (cobj[key], cobj_replacement, key))
        traversal.insert(0, (cobj_replacement, cparent, ckey))

    for titem in traversal:
        cobj, cparent, ckey = titem
        cparent[ckey] = cobj

    return ret[0]


in_ = attr.validators.in_
instance_of = attr.validators.instance_of
instance_of_str = instance_of(str)
optional = attr.validators.optional
optional_str = optional(instance_of_str)
