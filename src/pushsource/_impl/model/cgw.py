from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class CGWPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a Content Gateway (CGW) YAML file.

    For push items of this type, the :meth:`~pushsource.PushItem.src`
    attribute refers to a YAML file containing list of definitions
    for objects in Content Gateway.

    This library does not verify that the referenced YAML file is valid.

    """
