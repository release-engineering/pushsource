from .base import PushItem
from .. import compat_attr as attr


@attr.s()
class ErratumReference(object):
    """A reference within a :meth:`~ErratumPushItem.references` list."""

    href = attr.ib(type=str)
    """A URL."""

    id = attr.ib(type=str)
    """A short ID for the reference, unique within this erratum."""

    title = attr.ib(type=str)
    """A title for the reference; analogous to the 'title' attribute
    in HTML.
    """

    type = attr.ib(type=str, default="other")
    """Type of reference. This defines the expected target of the URL
    and includes at least:

    - "self": reference to a page for this advisory
    - "bugzilla": reference to a bug
    - "other": any other kind of reference
    """


@attr.s()
class ErratumModule(object):
    """A module entry within a :meth:`~ErratumPushItem.pkglist`."""

    arch = attr.ib(type=str)
    """Module architecture."""

    context = attr.ib(type=str)
    """Module context."""

    name = attr.ib(type=str)
    """Module name."""

    stream = attr.ib(type=str)
    """Module stream."""

    version = attr.ib(type=str)
    """Module version."""


@attr.s()
class ErratumPackage(object):
    """A package (RPM) entry within a :meth:`~ErratumPushItem.pkglist`."""

    arch = attr.ib(type=str)
    """RPM architecture."""

    filename = attr.ib(type=str)
    """RPM filename (basename)."""

    epoch = attr.ib(type=str)
    """RPM epoch."""

    name = attr.ib(type=str)
    """RPM name (e.g. "bash-4.0.1-1.el7.x86_64.rpm" name is "bash")"""

    version = attr.ib(type=str)
    """RPM version (e.g. "bash-4.0.1-1.el7.x86_64.rpm" version is "4.0.1")"""

    release = attr.ib(type=str)
    """RPM release (e.g. "bash-4.0.1-1.el7.x86_64.rpm" version is "1.el7")"""

    src = attr.ib(type=str)
    """Filename of the source RPM from which this RPM was built; equal to
    :meth:`filename` for the source RPM itself.
    """

    md5sum = attr.ib(type=str, default=None)
    """MD5 checksum of this RPM in hex string form, if available."""

    sha1sum = attr.ib(type=str, default=None)
    """SHA1 checksum of this RPM in hex string form, if available."""

    sha256sum = attr.ib(type=str, default=None)
    """SHA256 checksum of this RPM in hex string form, if available."""


@attr.s()
class ErratumPackageCollection(object):
    """A collection of packages found within an :meth:`~ErratumPushItem.pkglist`.

    A non-modular advisory typically contains only a single collection, while modular
    advisories typically contain one collection per module.
    """

    name = attr.ib(type=str)
    """A name for this collection. The collection name has no specific meaning,
    but must be unique within an advisory.
    """

    packages = attr.ib(type=list)
    """List of packages (:class:`ErratumPackage`) within this collection."""

    short = attr.ib(type=str, default="")
    """An alternative name for this collection. In practice, this field
    is typically blank.
    """

    module = attr.ib(type=ErratumModule, default=None)
    """An :class:`~ErratumModule` defining the module this entry is associated
    with, if any.
    """


@attr.s()
class ErratumPushItem(PushItem):
    """A push item representing a single erratum (also known as "advisory").

    Note that many fields on erratum objects which appear to be numeric
    are instead represented as strings ('release' and 'pushcount' being two
    examples).
    """

    type = attr.ib(type=str, default="bugfix")
    """Type of advisory: 'bugfix', 'security' or 'enhancement'."""

    release = attr.ib(type=str, default="0")
    """Release number. Typically an integer-string, initially '0'."""

    status = attr.ib(type=str, default="final")
    """Status, typically 'final'."""

    pushcount = attr.ib(type=str, default="1")
    """Number of times advisory has been revised and published (starting at '1')."""

    reboot_suggested = attr.ib(type=bool, default=False)
    """True if rebooting host machine is recommended after installing this advisory."""

    references = attr.ib(type=list, default=attr.Factory(list))
    """A list of references (:class:`ErratumReference`) associated with the advisory."""

    pkglist = attr.ib(type=list, default=attr.Factory(list))
    """A list of package collections (:class:`ErratumPackageCollection`)
    associated with the advisory."""

    from_ = attr.ib(type=str, default=None)
    """Contact email address for the owner of the advisory."""

    rights = attr.ib(type=str, default=None)
    """Copyright message."""

    title = attr.ib(type=str, default=None)
    """Title of the advisory (e.g. 'bash bugfix and enhancement')."""

    description = attr.ib(type=str, default=None)
    """Full human-readable description of the advisory, usually multiple lines."""

    version = attr.ib(type=str, default="1")
    """Advisory version. Starts counting at "1", and some systems require updating
    the version whenever an advisory is modified.
    """

    updated = attr.ib(type=str, default=None)
    """Timestamp of the last update to this advisory.

    Typically of the form '2019-12-31 06:54:41 UTC', but this is not enforced.
    """

    issued = attr.ib(type=str, default=None)
    """Timestamp of the initial release of this advisory.

    Uses the same format as :meth:`updated`.
    """

    severity = attr.ib(type=str, default=None)
    """Severity of the advisory, e.g. "low", "moderate", "important" or "critical"."""

    summary = attr.ib(type=str, default=None)
    """Typically a single sentence briefly describing the advisory."""

    solution = attr.ib(type=str, default=None)
    """Text explaining how to apply the advisory."""

    content_types = attr.ib(type=list, default=attr.Factory(list))
    """A list of content types associated with the advisory.

    For example, "docker" may be found in this list if the advisory deals
    with container images.
    """

    def __str__(self):
        return "%s: %s" % (self.name, self.title or "<untitled advisory>")
