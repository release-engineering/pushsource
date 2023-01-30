import re

from frozenlist2 import frozenlist

from .. import compat_attr as attr
from .conv import in_, instance_of, optional_str, optional
from .vms import VMIPushItem


VHDGeneration = ["V1", "V2"]


@attr.s()
class VHDPushItem(VMIPushItem):
    """A :class:`~pushsource.PushItem` representing a Virtual Hard Disk (or VHD).

    For push items of this type, the :meth:`~pushsource.PushItem.src` attribute
    refers to a file containing the VHD file..

    This library does not verify that the referenced file is a valid
    snapshot.

    Note: As some attributes can not be obtained directly from Koji they're marked
    as optional in the `attrs` validators. With this the VHDPushItem objects can be
    created without these attributes and the missing values can be added later by
    using `attrs.evolve`.
    """

    generation = attr.ib(type=str, default="V2", validator=optional(in_(VHDGeneration)))
    """VHD generation. It can be ``V1`` or ``V2``."""

    sku_id = attr.ib(type=str, default=None, validator=optional_str)
    """SKU ID for the VM image generation, generally being the Plan ID."""

    support_legacy = attr.ib(type=bool, default=False, validator=instance_of(bool))
    """If the image ``generation == V2`` but also supports ``V1``."""

    legacy_sku_id = attr.ib(type=str, default=None)
    """The ``V1`` SKU ID (only if ``support_legacy`` is true)."""

    disk_version = attr.ib(type=str, default=None)
    """The image's disk version according to Azure's format {int}.{int}.{int}"""

    recommended_sizes = attr.ib(
        type=list,
        default=attr.Factory(frozenlist),
        converter=lambda x: frozenlist(sorted(x)),
    )
    """List of recommended VM sizes in Azure, for example ['a1-standard', 'a5', 'a7']"""

    sas_uri = attr.ib(type=str, default=None, validator=optional_str)
    """The SAS URI to be associated with the disk_version."""

    @disk_version.validator
    def __validate_disk_version(self, attribute, value):
        # pylint: disable=unused-argument
        if value and not re.match(r"^(\d+\.)(\d+\.)(\*|\d+)$", value):
            raise ValueError(
                r"Invalid disk version. Expected format: {int}.{int}.{int}"
            )

    def __attrs_post_init__(self):
        if self.legacy_sku_id and not self.support_legacy:
            raise ValueError(
                'The attribute "legacy_sku_id" must only be set when'
                ' "support_legacy" is True.'
            )
