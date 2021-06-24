import hashlib
import os
import logging

from frozenlist2 import frozenlist

from .. import compat_attr as attr
from .conv import (
    md5str,
    sha256str,
    upper_if_str,
    instance_of_str,
    instance_of,
    optional_str,
)


LOG = logging.getLogger("pushsource")
CHUNKSIZE = int(os.environ.get("PUSHSOURCE_CHUNKSIZE") or 1024 * 1024 * 16)


@attr.s()
class KojiBuildInfo(object):
    """A representation of a koji build."""

    name = attr.ib(type=str, validator=instance_of_str)
    """'name' component of build's NVR.

    Example: in "kf5-kio-5.83.0-2.el8.next", the name is "kf5-kio".
    """

    version = attr.ib(type=str, validator=instance_of_str)
    """'version' component of build's NVR.

    Example: in "kf5-kio-5.83.0-2.el8.next", the version is "5.83.0".
    """

    release = attr.ib(type=str, validator=instance_of_str)
    """'release' component of build's NVR.

    Example: in "kf5-kio-5.83.0-2.el8.next", the release is "2.el8.next".
    """

    @classmethod
    def _from_nvr(cls, nvr_str):
        if not nvr_str:
            return

        # Initial state: 'kf5-kio-5.83.0-2.el8.next'
        # Reverse:       'txen.8le.2-0.38.5-oik-5fk'
        nvr_rev = nvr_str[::-1]

        # Split:         ['txen.8le.2', '0.38.5', 'oik-5fk']
        rvn_rev = nvr_rev.split("-", 2)

        # Unreverse:     ['2.el8.next', '5.83.0', 'kf5-kio']
        (r, v, n) = [s[::-1] for s in rvn_rev]

        return cls(name=n, version=v, release=r)


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

    :type: list[str]
    """

    md5sum = attr.ib(type=str, default=None, converter=md5str)
    """Hex digest of MD5 checksum for this push item, if available.

    .. seealso::

        :meth:`with_checksums`
    """

    sha256sum = attr.ib(type=str, default=None, converter=sha256str)
    """Hex digest of SHA256 checksum for this push item, if available.

    .. seealso::

        :meth:`with_checksums`
    """

    origin = attr.ib(type=str, default=None, validator=optional_str)
    """A string representing the origin of this push item.

    The "origin" field is expected to record some info on how this push item
    was discovered. The exact semantics depend on the specific source backend
    in use.
    """

    build = attr.ib(type=str, default=None, validator=optional_str)
    """NVR for the koji build from which this push item was extracted, if any.

    .. seealso::

        :meth:`build_info`, which provides the same info in parsed form.
    """

    build_info = attr.ib(
        type=KojiBuildInfo, validator=instance_of((KojiBuildInfo, type(None)))
    )
    """Basic info on the koji build from which this push item was extracted, if any."""

    @build_info.default
    def _default_build_info(self):
        return KojiBuildInfo._from_nvr(self.build)

    signing_key = attr.ib(
        type=str, default=None, validator=optional_str, converter=upper_if_str
    )
    """If this push item was GPG signed, this should be an identifier for the
    signing key used.

    Generally a short key ID such as "F21541EB" is used, though the library
    doesn't enforce this.
    """

    def with_checksums(self):
        """Return a copy of this push item with checksums present.

        Many pushsource backends will produce push items with empty checksum attributes,
        since checksum calculation may be expensive and may not be required in all cases.

        The rule of thumb is that a pushsource will only provide checksums if they were
        available in metadata, so that reading the push item's file was unnecessary.
        For example:

        - with ``errata`` push source, checksums are generally available by default, because
          Errata Tool itself provides checksums on the files contained in an advisory.
        - with ``staged`` push source, checksums are unavailable by default, because the
          sums can only be calculated by reading file content from the staging area.

        Where checksums are needed, this utility method may be used to ensure they are present
        regardless of the push source used.

        This method entails reading the entire content of the file referenced
        by this push item, and may be:

        - slow: may need to read a large file from a remote system, e.g. from an NFS volume.
        - error-prone: reads from a remote system might fail.

        As such, when dealing with a large number of push items, you may want to consider
        using multiple threads to parallelize calls to ``with_checksums``, and retrying
        failing operations.

        If checksums are already present or if this item does not reference a file, this
        method is a no-op and returns the current push item, unmodified.

        Returns:
            :class:`~pushsource.PushItem`
                A copy of this item, guaranteed either to have non-empty :meth:`md5sum` and
                :meth:`sha256sum` attributes, or an empty :meth:`src` attribute (denoting that
                the item does not reference a file).

        .. versionadded:: 1.2.0
        """
        if not self.src:
            return self

        hashers = []

        if not self.md5sum:
            hashers.append((hashlib.new("md5"), "md5sum"))
        if not self.sha256sum:
            hashers.append((hashlib.new("sha256"), "sha256sum"))

        if not hashers:
            # Nothing to do
            return self

        LOG.debug("Start read: %s", self.src)

        with open(self.src, "rb") as src_file:
            while True:
                chunk = src_file.read(CHUNKSIZE)
                if not chunk:
                    break
                for (hasher, _) in hashers:
                    hasher.update(chunk)

        LOG.debug("End read: %s", self.src)

        updated_sums = {}
        for (hasher, attribute) in hashers:
            updated_sums[attribute] = hasher.hexdigest()

        return attr.evolve(self, **updated_sums)
