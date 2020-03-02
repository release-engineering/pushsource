from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class ProductIdPushItem(PushItem):
    """A push item representing a product ID certificate.

    For push items of this type, the ``src`` attribute refers to a
    file containing a PEM certificate identifying a product.

    This library does not verify that the referenced file is a valid
    certificate.
    """
