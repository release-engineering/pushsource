from .base import PushItem
from .. import compat_attr as attr
from .conv import optional_str, convert_maybe


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

    display_order = attr.ib(type=float, default=None, converter=convert_maybe(float))
    """A display order hint associated with the file.

    This value is intended for display purposes only.
    In a UI presenting a file list, it is suggested that the default order
    of files should be set by an ascending sort using this value.
    This provides a method of keeping related files grouped together and
    presented to users in a logical order.

    .. versionadded:: 2.14.0
    """

    @display_order.validator
    def _check_order(self, _, value):
        if value is None:
            # OK as field is optional
            return

        # It has to be a float or convertible to float
        value = float(value)

        # Enforce some bounds:
        # - UD has used 99999 as a default "sort at end", so we'll make that the max
        #   permitted value.
        # - Pub's default set on push is 0, so most files in practice have that value.
        # - It's not clear if negative values have been used. However it seems we should
        #   allow them as otherwise there is no way to arrange for files to sort earlier
        #   than Pub's historical default.
        # - The lower bound may as well be symmetrical with the upper bound.
        # - This check will also filter out NaN.
        if not (value >= -99999 and value <= 99999):
            raise ValueError("display_order must be within range -99999 .. 99999")
