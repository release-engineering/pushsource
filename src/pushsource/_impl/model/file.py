from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class FilePushItem(PushItem):
    """A push item representing a single generic file."""

    description = attr.ib(type=str, default=None)
    """A human-readable brief description of the file."""
