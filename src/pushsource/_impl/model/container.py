from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class ContainerImagePushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a container image.

    This item represents any kind of image which can be pulled
    from a container image registry (i.e. an object identified by a
    ``NAME[:TAG|@DIGEST]`` string).

    In the case of a multi-arch image, one ContainerImagePushItem represents
    an image for a single architecture only.
    """


@attr.s()
class OperatorManifestPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing an operator manifests archive
    (typically named ``operator_manifests.zip``).
    """
