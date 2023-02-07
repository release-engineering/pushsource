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

    @classmethod
    def _from_data(cls, data):
        """Instantiate AmiRelease from raw dict"""

        kwargs = {
            "product": data["product"],
            "date": data["date"],
            "arch": data["arch"],
            "respin": int(data["respin"]),
            "version": data.get("version") or None,
            "base_product": data.get("base_product") or None,
            "base_version": data.get("base_version") or None,
            "variant": data.get("variant") or None,
            "type": data.get("type") or None,
        }
        return cls(**kwargs)


@attr.s()
class AmiBillingCodes(object):
    """Billing codes associated with an AMI."""

    name = attr.ib(type=str, default=None, validator=instance_of_str)
    """Billing codes name, for example Hourly2, arbitrary string for making image name unique."""

    codes = attr.ib(type=list, default=attr.Factory(frozenlist), converter=frozenlist)
    """List of billing codes, for example ['bp-1234abcd', 'bp-5678efgh'].

    :type: list[str]
    """

    @classmethod
    def _from_data(cls, data):
        """Instantiate AmiBillingCodes from raw dict"""

        kwargs = {
            "name": data["name"],
            "codes": data["codes"],
        }
        return cls(**kwargs)


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

    image_id = attr.ib(type=str, default=None, validator=optional_str)
    """AMI Image ID used to reference the image in AWS."""

    @classmethod
    def _from_data(cls, data):
        """Instantiate AmiPushItem from raw list or dict"""

        if isinstance(data, list):
            return [cls._from_data(elem) for elem in data]

        kwargs = {
            # base push item fields
            "name": data["name"],
            "state": "PENDING",
            "src": data.get("src") or None,
            "dest": data.get("dest") or [],
            "origin": data.get("origin") or None,
            # ami push item fields
            "release": AmiRelease._from_data(data.get("release") or {}),
            "type": data["type"],
            "region": data["region"],
            "virtualization": data["virtualization"],
            "volume": data["volume"],
            "root_device": data["root_device"],
            "description": data["description"],
            "sriov_net_support": data["sriov_net_support"],
            "ena_support": data.get("ena_support") or None,
            "billing_codes": AmiBillingCodes._from_data(
                data.get("billing_codes") or {}
            ),
            "image_id": data.get("ami") or None,
        }

        return cls(**kwargs)
