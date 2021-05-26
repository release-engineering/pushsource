import datetime

from frozenlist2 import frozenlist

from .base import PushItem
from .. import compat_attr as attr
from .conv import datestr, instance_of_str, instance_of, optional_str, optional


@attr.s()
class AmiRelease(object):
    """Release metadata associated with an AMI."""

    product = attr.ib(type=str, validator=instance_of_str)
    """A short product name, for example "RHEL" if this is an image for Red Hat
    Enterprise Linux."""

    date = attr.ib(type=datetime.date, converter=datestr)
    """Date at which this image was generated."""

    arch = attr.ib(type=str, validator=instance_of_str)
    """Architecture of the image, for example "x86_64"."""

    respin = attr.ib(type=int, validator=instance_of(int))
    """Respin count. 0 for original build of an image, incremented by one for
    each rebuild."""

    version = attr.ib(type=str, default=None, validator=optional_str)
    """A <major>.<minor> version string for the image's product version, for example
    "7.9" if this is an image for Red Hat Enterprise Linux 7.9.x."""

    base_product = attr.ib(type=str, default=None, validator=optional_str)
    """For layered products, name of the base product for which the image should be used."""

    base_version = attr.ib(type=str, default=None, validator=optional_str)
    """For layered products, version of the base product for which the image should be used."""

    variant = attr.ib(type=str, default=None, validator=optional_str)
    """Variant of this image's product (only for products which have variants).  For example,
    "Server", for Red Hat Enterprise Linux Server."""

    type = attr.ib(type=str, default=None, validator=optional_str)
    """Release type, typically "ga" or "beta"."""


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
class AmiPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing an Amazon Machine Image (or "AMI").

    For push items of this type, the :meth:`~pushsource.PushItem.src` attribute
    refers to a file containing an EBS snapshot.  The push item contains additional
    metadata which can be used to associate the snapshot with an image.

    This library does not verify that the referenced file is a valid
    snapshot.
    """

    release = attr.ib(
        type=AmiRelease, default=None, validator=optional(instance_of(AmiRelease))
    )
    """Release metadata associated with this image."""

    type = attr.ib(type=str, default=None, validator=optional_str)
    """Billing type associated with the image, e.g. "hourly" or "access"."""

    region = attr.ib(type=str, default=None, validator=instance_of_str)
    """Region to which this image should be pushed."""

    virtualization = attr.ib(type=str, default=None, validator=instance_of_str)
    """Virtualization type, e.g. "hvm" or "pv"."""

    volume = attr.ib(type=str, default=None, validator=instance_of_str)
    """EBS volume type, e.g. "gp2" or "io1"."""

    root_device = attr.ib(type=str, default=None, validator=instance_of_str)
    """Root device node used with this image, e.g. "/dev/sda1"."""

    description = attr.ib(type=str, default=None, validator=instance_of_str)
    """A brief human-readable description of the image."""

    sriov_net_support = attr.ib(type=str, default=None, validator=instance_of_str)
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
