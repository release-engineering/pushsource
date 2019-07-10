from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class RpmPushItem(PushItem):
    """A push item representing a single RPM."""

    # no RPM-specific metadata is implemented yet; the class exists
    # only for the purpose of instanceof checks
