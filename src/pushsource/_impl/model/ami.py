from frozenlist2 import frozenlist

from .. import compat_attr as attr
from .conv import instance_of_str, instance_of, optional_str, optional
from .vms import VMIRelease, VMIPushItem


class AmiRelease(VMIRelease):
    """
    Release metadata associated with an AMI.

    This class has the same attributes as VMIRelease and it's only kept
    for backwards compatibility.
    """


@attr.s()
class AmiBillingCodes(object):
    """Billing codes associated with an AMI."""

    name = attr.ib(type=str, default=None, validator=instance_of_str)
    """Billing codes name, for example Hourly2, arbitrary string for making image name unique."""

    codes = attr.ib(type=list, default=attr.Factory(frozenlist), converter=frozenlist)
    """List of billing codes, for example ['bp-1234abcd', 'bp-5678efgh'].

    :type: list[str]
    """


@attr.s()
class AmiPushItem(VMIPushItem):
    """A :class:`~pushsource.PushItem` representing an Amazon Machine Image (or "AMI").

    For push items of this type, the :meth:`~pushsource.PushItem.src` attribute
    refers to a file containing an EBS snapshot.  The push item contains additional
    metadata which can be used to associate the snapshot with an image.

    This library does not verify that the referenced file is a valid
    snapshot.
    """

    _RELEASE_TYPE = AmiRelease

    type = attr.ib(type=str, default=None, validator=optional_str)
    """Billing type associated with the image, e.g. "hourly" or "access"."""

    region = attr.ib(type=str, default=None, validator=optional_str)
    """Region to which this image should be pushed."""

    virtualization = attr.ib(type=str, default=None, validator=optional_str)
    """Virtualization type, e.g. "hvm" or "pv"."""

    volume = attr.ib(type=str, default=None, validator=optional_str)
    """EBS volume type, e.g. "gp2" or "io1"."""

    root_device = attr.ib(type=str, default=None, validator=optional_str)
    """Root device node used with this image, e.g. "/dev/sda1"."""

    sriov_net_support = attr.ib(type=str, default=None, validator=optional_str)
    """"simple" if the image is SRIOV-enabled."""

    ena_support = attr.ib(
        type=bool, default=None, validator=optional(instance_of(bool))
    )
    """``True`` if the image supports Elastic Network Adapter (ENA)."""

    billing_codes = attr.ib(
        type=AmiBillingCodes,
        default=None,
        validator=optional(instance_of(AmiBillingCodes)),
    )
    """Billing codes associated with this image."""
