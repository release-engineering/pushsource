from .base import PushItem
from .conv import optional_str
from .. import compat_attr as attr


@attr.s()
class RpmPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a single RPM."""

    module_build = attr.ib(type=str, default=None, validator=optional_str)
    """NVR for the koji module build through which this push item was located, if any.

    For a modular RPM push item, there may be two koji builds in play:

    ``module_build`` (this attribute):
        NVR of a build which produced modulemd YAML files referencing this RPM
        (but the build itself does not contain RPMs).

        Example: `ghc-8.4-820200708061905.9edba152`_
        is a valid `module_build` for ``ghc-8.4.4-74.module_el8+12161+cf1bd7f2.x86_64.rpm``.

    :meth:`~pushsource.PushItem.build`:
        NVR of the build containing the RPM.

        Example: `ghc-8.4.4-74.module_el8+12161+cf1bd7f2`_
        is a valid build for ``ghc-8.4.4-74.module_el8+12161+cf1bd7f2.x86_64.rpm``.

    Note that the ``module_build`` itself isn't a property of the RPM but rather should
    be considered contextual information on how any given RPM was located. The same RPM
    may have different values of ``module_build`` when loaded from different contexts.

    .. _ghc-8.4-820200708061905.9edba152: https://koji.fedoraproject.org/koji/buildinfo?buildID=1767200
    .. _ghc-8.4.4-74.module_el8+12161+cf1bd7f2: https://koji.fedoraproject.org/koji/buildinfo?buildID=1767130
    """
