from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class CompsXmlPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a comps XML file.

    For push items of this type, the :meth:`~pushsource.PushItem.src`
    attribute refers to a file containing a comps XML file (package
    group definitions) in the format used by yum & dnf.

    This library does not verify that the referenced file is valid.
    """
