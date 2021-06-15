from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class ModuleMdPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a modulemd stream.

    For push items of this type, the :meth:`~pushsource.PushItem.src` attribute
    refers to a file containing a YAML document stream. The stream is expected
    to contain one or more modulemd or modulemd-defaults documents.

    This library does not verify that the referenced file is a valid
    modulemd stream.
    """


@attr.s()
class ModuleMdSourcePushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a modulemd source/packager document.

    Similar to :class:`~pushsource.ModuleMdPushItem`, but refers to the source
    document, typically named ``modulemd.src.txt`` in koji.

    This library does not verify that the referenced file is a valid
    modulemd source document.
    """
