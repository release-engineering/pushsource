from frozenlist2 import frozenlist

from .. import compat_attr as attr
from .conv import instance_of_str, instance_of, optional_str, optional
from .vms import VMIRelease, VMIPushItem, BootMode


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
class AmiSecurityGroup(object):
    """Security group information to be associated with a Marketplace VM."""

    from_port = attr.ib(type=int, validator=instance_of(int))
    """If the protocol is TCP or UDP, this is the start of the port range.
    If the protocol is ICMP or ICMPv6, this is the type number.
    A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types,
    you must specify all ICMP/ICMPv6 codes."""

    ip_protocol = attr.ib(type=str, validator=instance_of_str)
    """The IP protocol name ( tcp , udp , icmp , icmpv6 )."""

    ip_ranges = attr.ib(type=list, converter=frozenlist)
    """List of the IPv4 ranges, for example ['22.22.22.22', '33.33.33.33'].

    :type: list[str]
    """

    to_port = attr.ib(type=int, validator=instance_of(int))
    """If the protocol is ICMP or ICMPv6, this is the code.
    A value of -1 indicates all ICMP/ICMPv6 codes.
    If you specify all ICMP/ICMPv6 types, you must specify all ICMP/ICMPv6 codes.."""

    @classmethod
    def _from_data(cls, data):
        """Instantiate SecurityGroup from raw dict"""

        kwargs = {
            "from_port": data["from_port"],
            "ip_protocol": data["ip_protocol"],
            "ip_ranges": data["ip_ranges"],
            "to_port": data["to_port"],
        }
        return cls(**kwargs)


@attr.s()
class AmiAccessEndpointUrl(object):
    """Access Endpoint URL to be associated with a Marketplace VM."""

    port = attr.ib(type=int, validator=instance_of(int))
    """Port to access the endpoint URL."""

    protocol = attr.ib(type=str, validator=instance_of_str)
    """Protocol to access the endpoint URL (http, https)."""

    @classmethod
    def _from_data(cls, data):
        """Instantiate AccessEndpointUrl from raw dict"""

        kwargs = {
            "port": data["port"],
            "protocol": data["protocol"],
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

    uefi_support = attr.ib(
        type=bool, default=None, validator=optional(instance_of(bool))
    )
    """``True`` if the image supports UEFI boot."""

    billing_codes = attr.ib(
        type=AmiBillingCodes,
        default=None,
        validator=optional(instance_of(AmiBillingCodes)),
    )
    """Billing codes associated with this image."""

    release_notes = attr.ib(type=str, default=None, validator=optional_str)
    """"Notes regarding changes in the newest version."""

    usage_instructions = attr.ib(type=str, default=None, validator=optional_str)
    """Step by step instructions for the end-user to launch, configure and access the product.

    Write with a less-technical customer in mind.
    """

    recommended_instance_type = attr.ib(type=str, default=None, validator=optional_str)
    """Recommended instance type for AMI e.g. "t2.micro", "r6a.large" """

    marketplace_entity_type = attr.ib(type=str, default=None, validator=optional_str)
    """Type of entity e.g. "AMIProduct", "SaasProduct", "ServerProduct". """

    image_id = attr.ib(type=str, default=None, validator=optional_str)
    """AMI Image ID used to reference the image in AWS."""

    public_image = attr.ib(
        type=bool, default=None, validator=optional(instance_of(bool))
    )
    """``True`` if the image is allowed to be released publicly (shared with group "all")."""

    scanning_port = attr.ib(
        type=int, default=None, validator=optional(instance_of(int))
    )
    """AMI scanning port, used when importing the AMI into AWS Marketplace to validate the AMI."""

    user_name = attr.ib(type=str, default=None, validator=optional_str)
    """The username used to login to the AMI. (Usually set to ec2-user)"""

    version_title = attr.ib(type=str, default=None, validator=optional_str)
    """The title given to a version. This will display in AWS Marketplace as the name of the version."""

    security_groups = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """Automatically created security groups for the product. """

    access_endpoint_url = attr.ib(
        type=AmiAccessEndpointUrl,
        default=None,
        validator=optional(instance_of(AmiAccessEndpointUrl)),
    )
    """Access endpoint url associated with this image."""

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
            "ena_support": data.get("ena_support"),
            "uefi_support": data.get("uefi_support"),
            "boot_mode": (
                BootMode(data.get("boot_mode")) if data.get("boot_mode") else None
            ),
            "billing_codes": AmiBillingCodes._from_data(
                data.get("billing_codes") or {}
            ),
            "image_id": data.get("ami") or None,
            "public_image": data.get("public_image"),
            "release_notes": data.get("release_notes") or None,
            "usage_instructions": data.get("usage_instructions") or None,
            "recommended_instance_type": data.get("recommended_instance_type") or None,
            "marketplace_entity_type": data.get("marketplace_entity_type") or None,
            "scanning_port": data.get("scanning_port") or None,
            "user_name": data.get("user_name") or None,
            "version_title": data.get("version_title") or None,
            "marketplace_title_template": data.get("marketplace_title_template")
            or None,
            "security_groups": [
                AmiSecurityGroup._from_data(security_group)
                for security_group in (data.get("security_groups") or [])
            ],
            "access_endpoint_url": (
                AmiAccessEndpointUrl._from_data(data.get("access_endpoint_url"))
                if data.get("access_endpoint_url")
                else None
            ),
        }

        return cls(**kwargs)
