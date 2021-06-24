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

    dest_signing_key = attr.ib(
        type=str, default=None, converter=lambda s: s.lower() if s else None
    )
    """Desired signing key for this container image.

    Typically a 16-character identifier for a signing key, such
    as ``"199e2f91fd431d51"``, though the format is not enforced
    by this library.

    A non-empty value for this attribute should be interpreted as a request to
    use the specified key to generate signatures for this image's manifest(s).
    See `container-signature`_ docs for information on signatures.

    .. _container-signature: https://github.com/containers/image/blob/33bcba75bb181318608f989e18e086f0d83d254c/docs/containers-signature.5.md
    """


@attr.s()
class SourceContainerImagePushItem(ContainerImagePushItem):
    """A :class:`~pushsource.PushItem` representing a source container image.

    Source container images are a special type of image which are not runnable
    but instead contain the packaged source code of a related binary image.

    See `this article <https://access.redhat.com/articles/3410171>`_ for more
    information on source container images.
    """


@attr.s()
class OperatorManifestPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing an operator manifests archive
    (typically named ``operator_manifests.zip``).
    """
