import datetime
import enum

from .base import PushItem
from .. import compat_attr as attr
from attr import asdict
from .conv import (
    convert_maybe,
    datestr,
    instance_of_str,
    instance_of,
    optional_str,
    optional,
)


class BootMode(enum.Enum):
    """Represent the possible boot modes for VM images."""

    hybrid = "hybrid"
    """Supports both UEFI and BIOS mode."""

    uefi = "uefi"
    """Supports only UEFI mode."""

    legacy = "legacy"
    """Supports only BIOS mode."""

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"{cls_name}.{self.name}"


@attr.s()
class VMICloudInfo(object):
    """Information on the cloud provider associated with a given push item.

    Cloud provider information is only available for VMIs which have previously
    been published to a cloud. It may be used to locate an existing VMI for
    manipulation, such as metadata updates or deletion.

    This library doesn't define any specific cloud provider names or aliases.
    Generally, a user of this library is expected to use the information here
    to look up cloud access details from a configuration file or other source.
    """

    provider = attr.ib(type=str, validator=instance_of_str)
    """The cloud provider's name, e.g.: "aws"."""

    account = attr.ib(type=str, validator=instance_of_str)
    """The cloud provider's account alias, e.g.: "aws-na"."""


@attr.s()
class VMIRelease(object):
    """Release metadata associated with a VM image."""

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

    @classmethod
    def _from_data(cls, data):
        """Instantiate VMIRelease from raw dict"""

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
class VMIPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a generic VM image.

    This class is used as a parent class for different types of VM images.
    """

    _RELEASE_TYPE = VMIRelease
    """The expected release type for this class."""

    release = attr.ib(default=None)
    """Release metadata associated with this image."""

    description = attr.ib(type=str, default=None, validator=instance_of_str)
    """A brief human-readable description of the image."""

    boot_mode = attr.ib(type=BootMode, default=None, converter=convert_maybe(BootMode))
    """Boot mode supported by the image (if known): uefi, legacy, or hybrid (uefi + legacy)."""

    cloud_info = attr.ib(
        type=VMICloudInfo,
        default=None,
        validator=optional((instance_of(VMICloudInfo))),
    )
    """Cloud provider information, such as the provider's short name and account alias."""

    marketplace_title_template = attr.ib(type=str, default=None, validator=optional_str)
    """The template is of the form used by ``str.format``, with available keywords being all of
    the documented fields on ``VMIRelease`` and ``AMIRelease`` classes.
    
    It's used by the property `marketplace_title` to format it as the marketplace title."""

    marketplace_name = attr.ib(type=str, default=None, validator=optional_str)
    """Name of the marketplace where the Image is expected to be shipped."""

    @property
    def marketplace_title(self) -> str:
        """The marketplace title which is used for some certain layered products.

        It's built from the `marketplace_title_template` by formatting it with the proper values.
        """
        if not self.marketplace_title_template or not self.release:
            return ""
        return self.marketplace_title_template.format(**asdict(self.release))

    @release.validator
    def __validate_release(self, attribute, value):  # pylint: disable=unused-argument
        # Strict (unidiomatic) type check ensures that subclasses
        # of VMIRelease can not be associated with VHDPushItem
        if (
            value and type(value) is not self._RELEASE_TYPE
        ):  # pylint: disable=unidiomatic-typecheck
            raise ValueError(
                'The release type must be "%s"' % self._RELEASE_TYPE.__name__
            )
