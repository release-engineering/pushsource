import datetime
from frozenlist2 import frozenlist
from .file import FilePushItem
from .. import compat_attr as attr

from .conv import sloppyintlist, sloppylist, timestamp, optional_str, instance_of


@attr.s()
class ChannelDumpPushItem(FilePushItem):
    """A :class:`~pushsource.FilePushItem` representing a channel dump file.

    A channel dump is a special type of ISO disc image containing
    channels exported from RHN Classic.
    """

    arch = attr.ib(type=str, default=None, validator=optional_str)
    """Architecture of this channel dump (e.g. "x86_64")."""

    eng_product_ids = attr.ib(
        type=list, converter=sloppyintlist, default=attr.Factory(frozenlist)
    )
    """Engineering product ID(s) (integers) associated with this channel dump."""

    content = attr.ib(type=str, default=None, validator=optional_str)
    """Brief label for content within this channel dump."""

    datetime = attr.ib(type=datetime.datetime, converter=timestamp, default=None)
    """UTC date/time at which this channel dump was generated."""

    disk_number = attr.ib(type=int, default=1, validator=instance_of(int))
    """Disk number. May be a value greater than 1 where a channel dump
    spans multiple disk images."""

    channels = attr.ib(
        type=list, converter=sloppylist, default=attr.Factory(frozenlist)
    )
    """List of RHN Classic channel(s) included in this channel dump."""

    product_name = attr.ib(type=str, default=None, validator=optional_str)
    """Name of the primary product included in this channel dump."""

    product_version = attr.ib(type=str, default=None, validator=optional_str)
    """Version of the primary product included in this channel dump."""

    type = attr.ib(type=str, default=None, validator=optional_str)
    """Type of the channel dump:

    - "base": channel dump is intended for standalone use, contains all
              content from dumped channels
    - "incremental": channel dump is intended for use in combination with
              earlier "base" dump, contains only a subset of content
    """
