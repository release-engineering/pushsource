import datetime

from .base import PushItem
from .. import compat_attr as attr
from .conv import datestr


@attr.s()
class AmiRelease(object):
    """Release metadata associated with an AMI."""

    # TODO: document these
    product = attr.ib(type=str)
    date = attr.ib(type=datetime.date, converter=datestr)
    arch = attr.ib(type=str)
    respin = attr.ib(type=int)
    version = attr.ib(type=str, default=None)
    base_product = attr.ib(type=str, default=None)
    base_version = attr.ib(type=str, default=None)
    variant = attr.ib(type=str, default=None)
    type = attr.ib(type=str, default=None)


@attr.s()
class AmiPushItem(PushItem):
    """A push item representing an Amazon Machine Image (or "AMI").

    For push items of this type, the ``src`` attribute refers to a
    file containing an EBS snapshot.  The push item contains additional
    metadata which can be used to associate the snapshot with an image.

    This library does not verify that the referenced file is a valid
    snapshot.
    """

    # TODO: document these
    release = attr.ib(type=AmiRelease, default=None)
    type = attr.ib(type=str, default=None)
    region = attr.ib(type=str, default=None)
    virtualization = attr.ib(type=str, default=None)
    volume = attr.ib(type=str, default=None)
    root_device = attr.ib(type=str, default=None)
    description = attr.ib(type=str, default=None)
    sriov_net_support = attr.ib(type=str, default=None)
    ena_support = attr.ib(type=bool, default=None)
