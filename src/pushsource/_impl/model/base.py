from frozenlist2 import frozenlist

from .. import compat_attr as attr
from .conv import md5str, sha256str, upper_if_str, instance_of_str, optional_str


@attr.s()
class PushItem(object):
    """A PushItem represents a single piece of content to be published.
    This may be an RPM, an advisory, a generic file, and so on.
    """

    name = attr.ib(type=str, validator=instance_of_str)
    """A name for this push item.

    A push item's name may be any short identifying string which is meaningful
    to end-users.

    In the common case of a regular file, a push item name will simply be a filename,
    optionally including leading path components.

    Container image manifests may provide their digest as the name.

    In all cases, a non-empty name must be provided.
    """

    state = attr.ib(type=str, default="PENDING")
    """The state of this push item.

    In the majority of cases, push sources will produce push items with
    a state of ``PENDING``, with the caller expected to later evolve the state.

    In rare cases, push sources may produce push items with other states, such
    as ``INVALIDFILE`` to indicate that the source located invalid content.
    """

    src = attr.ib(type=str, default=None, validator=optional_str)
    """The source of this push item.

    If the push item is a file, this will be the full path to the file.
    If the push item does not represent a file, this will generally be omitted.
    """

    dest = attr.ib(type=list, default=attr.Factory(frozenlist), converter=frozenlist)
    """Destination of this push item.

    The meaning of "dest" differs depending on the source used and its configuration.

    Examples for possible uses of "dest" include:

    * a path to a directory (for items pushed using rsync)
    * a Pulp repository name (for items pushed using Pulp)
    """

    md5sum = attr.ib(type=str, default=None, converter=md5str)
    """Hex digest of MD5 checksum for this push item, if available."""

    sha256sum = attr.ib(type=str, default=None, converter=sha256str)
    """Hex digest of SHA256 checksum for this push item, if available."""

    origin = attr.ib(type=str, default=None, validator=optional_str)
    """A string representing the origin of this push item.

    The "origin" field is expected to record some info on how this push item
    was discovered. The exact semantics depend on the specific source backend
    in use.
    """

    build = attr.ib(type=str, default=None, validator=optional_str)
    """NVR for the koji build from which this push item was extracted, if any."""

    signing_key = attr.ib(
        type=str, default=None, validator=optional_str, converter=upper_if_str
    )
    """If this push item was GPG signed, this should be an identifier for the
    signing key used.

    Generally a short key ID such as "F21541EB" is used, though the library
    doesn't enforce this.
    """
