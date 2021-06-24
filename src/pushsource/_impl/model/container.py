import re

import six
from frozenlist2 import frozenlist

from .base import PushItem
from .. import compat_attr as attr
from ..compat import frozendict
from .conv import instance_of, optional_str


MEDIA_TYPE_ORDER = {
    "application/vnd.docker.distribution.manifest.list.v2+json": 30,
    "application/vnd.docker.distribution.manifest.v2+json": 20,
    "application/vnd.docker.distribution.manifest.v1+json": 10,
}


@attr.s()
class ContainerImagePullSpec(object):
    """A container image pull spec in parsed form.

    Pull spec refers to a ``"NAME[:TAG|@DIGEST]"`` string used to pull
    a container image. This class provides a pull spec both in raw
    string form and parsed into various components, along with information
    on the available media type.
    """

    registry = attr.ib(type=str, validator=instance_of(six.string_types))
    """Registry component of pull spec.

    Example: in ``"registry.access.redhat.com/ubi8/ubi-minimal:latest"``,
    the registry is ``"registry.access.redhat.com"``.
    """

    repository = attr.ib(type=str, validator=instance_of(six.string_types))
    """Repository component of pull spec.

    Example: in ``"registry.access.redhat.com/ubi8/ubi-minimal:latest"``,
    the repository is ``"ubi8/ubi-minimal"``.
    """

    @classmethod
    def _from_str(cls, pull_spec):
        # Regex explanation
        # <registry>: Get everything not "/" until the first "/"
        # <repository>: Get everything not "@" or ":"
        # <type>: Either '@' or ':'
        # <digest_or_tag>: Get the rest of the characters until end of word
        url_pattern = (
            r"^(?P<registry>[^\/]+)\/(?P<repository>[^:@]+)"
            r"(?P<type>[:@])(?P<digest_or_tag>.+)$"
        )
        match = re.match(url_pattern, pull_spec)
        if not match:
            raise ValueError("Invalid container image pull spec '%s'" % pull_spec)

        out = {
            "registry": match.group("registry"),
            "repository": match.group("repository"),
        }
        if match.group("type") == "@":
            out["digest"] = match.group("digest_or_tag")
            klass = ContainerImageDigestPullSpec
        else:
            out["tag"] = match.group("digest_or_tag")
            klass = ContainerImageTagPullSpec

        return klass(**out)


@attr.s()
class ContainerImageTagPullSpec(ContainerImagePullSpec):
    """A container image pull spec using a tag."""

    tag = attr.ib(type=str, validator=instance_of(six.string_types))
    """Tag component of pull spec.

    Example: in ``"registry.access.redhat.com/ubi8/ubi-minimal:latest"``,
    the tag is ``"latest"``.
    """

    media_types = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """Media type(s) expected to be reachable via this tag, or empty
    if unknown.

    Generally, the media types are only known for manifest lists obtained
    from a koji build.

    Example: ``["application/vnd.docker.distribution.manifest.list.v2+json"]``

    :type: List[str]
    """

    def __str__(self):
        return "".join([self.registry, "/", self.repository, ":", self.tag])


@attr.s()
class ContainerImageDigestPullSpec(ContainerImagePullSpec):
    """A container image pull spec using a manifest digest."""

    digest = attr.ib(type=str, validator=instance_of(six.string_types))
    """Digest component of pull spec.

    Example: in ``"registry.access.redhat.com/ubi8/ubi-minimal@sha256:0ccb9988abbc72d383258d58a7f519a10b637d472f28fbca6eb5fab79ba82a6b"``,
    the digest is ``"sha256:0ccb9988abbc72d383258d58a7f519a10b637d472f28fbca6eb5fab79ba82a6b"``.
    """

    media_type = attr.ib(type=str, default=None, validator=optional_str)
    """Media type of the manifest obtained by this pull spec, if known.

    Generally, the media type is known for all digest pull specs obtained
    via koji. It can be checked to determine whether a pull spec refers to
    a manifest list or an image manifest.

    Example: ``"application/vnd.docker.distribution.manifest.v2+json"``
    """

    def __str__(self):
        return "".join([self.registry, "/", self.repository, "@", self.digest])


def specs_converter(specs, expected_class):
    # a converter for pull specs, ensures every spec is an
    # instance of the expected class while de-duplicating
    out = []

    out_strs = set()
    for spec in specs:
        if not isinstance(spec, expected_class):
            raise TypeError("Expected %s, got: %s" % (expected_class, repr(spec)))

        # de-duplicate specs
        if str(spec) not in out_strs:
            out_strs.add(str(spec))
            out.append(spec)

    return frozenlist(out)


def tag_specs_converter(specs):
    out = specs_converter(specs, ContainerImageTagPullSpec)

    # Require at least one
    if not out:
        raise ValueError("A container image must have at least one pull spec")

    return out


def digest_specs_converter(specs):
    # Do the generic handling
    out = specs_converter(specs, ContainerImageDigestPullSpec)

    # Then also sort them by preferred media types
    out = sorted(out, key=lambda spec: -MEDIA_TYPE_ORDER.get(spec.media_type, 0))

    return frozenlist(out)


@attr.s()
class ContainerImagePullInfo(object):
    """Information needed to access a container image from a registry."""

    tag_specs = attr.ib(type=list, converter=tag_specs_converter)
    """Pull specs to access this image by tag.

    This may include specs which refer to a *manifest list* referencing this
    image, and also specs which refer directly to the *image manifest* for
    this image.

    This field always contains at least one pull spec. If you don't care
    which tag you use, it's reasonable to use ``item.pull_info.tag_specs[0]``.

    Note that, as all tags are mutable, it's possible for this information to
    be outdated. It is recommended to pull by digest or at least
    cross-reference with digests.

    :type: List[ContainerImageTagPullSpec]
    """

    digest_specs = attr.ib(type=list, converter=digest_specs_converter)
    """Pull specs to access this image by manifest digest.

    This may include specs which refer to a *manifest list* referencing this
    image, and also specs which refer directly to the *image manifest* for
    this image.

    These specs are always ordered from most to least preferred manifest type,
    which means:

    - manifest list if available, else:
    - schema2 image manifest if available, else:
    - schema1 image manifest

    :type: List[ContainerImageDigestPullSpec]
    """

    media_types = attr.ib(type=list, converter=frozenlist)
    """All media types for which a manifest is reachable in :meth:`digest_specs`.

    For information on these types see the `image manifest spec`_.

    :type: List[str]

    .. _image manifest spec: http://web.archive.org/web/20210614172014/https://docs.docker.com/registry/spec/manifest-v2-2/#media-types
    """

    @media_types.default
    def _default_media_types(self):
        return frozenlist(
            [spec.media_type for spec in self.digest_specs if spec.media_type]
        )

    def digest_spec_for_type(self, media_type):
        """Get the digest spec for a specific media type, if available.

        Parameters:
            media_type (str)
                a MIME type string identifying a type of image manifest or
                manifest list, e.g. "application/vnd.docker.distribution.manifest.v2+json"

        Returns:
            :class:`ContainerImageDigestPullSpec`
                if a digest of the requested type is available
            ``None``
                if a digest of the requested type is not available
        """
        for spec in self.digest_specs:
            if spec.media_type == media_type:
                return spec


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

    source_tags = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """Tags placed onto this image when it was built, if known.

    :type: List[str]
    """

    labels = attr.ib(type=dict, default=attr.Factory(frozendict), converter=frozendict)
    """Labels of this image, if known.

    This field is not guaranteed to include all labels associated with the image.

    :type: Dict[str, str]
    """

    arch = attr.ib(type=str, default=None)
    """Architecture of this image, if known.

    This field uses the conventional architecture strings used throughout the
    container ecosystem, such as ``"amd64"``.
    """

    pull_info = attr.ib(
        type=ContainerImagePullInfo,
        default=None,
        validator=instance_of(ContainerImagePullInfo),
    )
    """Metadata for pulling this image from a registry."""


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
