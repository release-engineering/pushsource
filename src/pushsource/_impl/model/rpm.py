from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class RpmPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a single RPM."""
