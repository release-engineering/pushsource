from .base import PushItem
from .. import compat_attr as attr
from ..utils.openers import open_src_local


@attr.s()
class DirectoryPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a directory.

    On a directory push item, the src attribute contains the full path to a directory tree.
    It should generally be interpreted as a request to recursively publish that entire directory
    tree as-is."""

    opener = attr.ib(type=callable, default=open_src_local, repr=False)
    """Identical to :attr:`~pushsource.PushItem.opener`.

    This defaults to reading content as file from :attr:`~pushsource.PushItem.src`
    
    .. versionadded:: 2.51.0
    """
