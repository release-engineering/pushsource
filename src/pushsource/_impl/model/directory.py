from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class DirectoryPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a directory.

    On a directory push item, the src attribute contains the full path to a directory tree.
    It should generally be interpreted as a request to recursively publish that entire directory
    tree as-is."""
