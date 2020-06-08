from .base import PushItem
from .. import compat_attr as attr
from .conv import optional_str


@attr.s()
class FilePushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a single generic file."""

    description = attr.ib(type=str, default=None, validator=optional_str)
    """A human-readable brief description of the file."""

    version = attr.ib(type=str, default=None, validator=optional_str)
    """A version string associated with the file.

    This string is intended for display purposes only.
    It may denote a product version associated with this file.
    For example, a push item for ``oc-4.2.33-linux.tar.gz`` may
    use a version of ``"4.2.33"`` to denote that the file relates
    to OpenShift version 4.2.33.
    """
