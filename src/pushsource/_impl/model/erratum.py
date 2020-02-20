from frozenlist2 import frozenlist

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

    @classmethod
    def _from_data(cls, data):
        # Convert from raw list/dict as provided in ET APIs into model
        if isinstance(data, list):
            return [cls._from_data(elem) for elem in data]

        return cls(
            href=data["href"], id=data["id"], title=data["title"], type=data["type"]
        )


@attr.s()
class ErratumModule(object):
    """A module entry within a :meth:`~ErratumPushItem.pkglist`."""

    name = attr.ib(type=str)
    """Module name."""

    stream = attr.ib(type=str)
    """Module stream."""

    version = attr.ib(type=str)
    """Module version."""

    context = attr.ib(type=str)
    """Module context."""

    arch = attr.ib(type=str)
    """Module architecture."""

    def __str__(self):
        return ":".join([self.name, self.stream, self.version, self.context, self.arch])

    @classmethod
    def _from_data(cls, data):
        if not data:
            return None
        return cls(
            arch=data["arch"],
            context=data["context"],
            name=data["name"],
            stream=data["stream"],
            version=data["version"],
        )


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

    packages = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """List of packages (:class:`ErratumPackage`) within this collection."""

    short = attr.ib(type=str, default="")
    """An alternative name for this collection. In practice, this field
    is typically blank.
    """

    module = attr.ib(type=ErratumModule, default=None)
    """An :class:`~ErratumModule` defining the module this entry is associated
    with, if any.
    """

    @classmethod
    def _from_data(cls, data):
        # Convert from raw list/dict as provided in ET APIs into model.
        # Data is expected to be 'pkglist' object.
        if isinstance(data, list):
            out = [cls._from_data(elem) for elem in data]
            # only include non-empty collections
            return [elem for elem in out if elem.packages]

        packages = []
        for raw_pkg in data.get("packages") or []:
            # parse the odd 'sum' structure, which is a list of form:
            # [<algo>, <hexdigest>, <algo>, <hexdigest>, ...]
            sums = {}
            raw_sum = raw_pkg.pop("sum", [])
            while raw_sum:
                sums[raw_sum[0]] = raw_sum[1]
                raw_sum = raw_sum[2:]

            packages.append(
                ErratumPackage(
                    arch=raw_pkg["arch"],
                    epoch=raw_pkg["epoch"],
                    filename=raw_pkg["filename"],
                    name=raw_pkg["name"],
                    version=raw_pkg["version"],
                    release=raw_pkg["release"],
                    src=raw_pkg["src"],
                    md5sum=sums.get("md5"),
                    sha1sum=sums.get("sha1"),
                    sha256sum=sums.get("sha256"),
                )
            )

        return cls(
            name=data["name"],
            short=data["short"],
            packages=packages,
            module=ErratumModule._from_data(data.get("module")),
        )


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

    references = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """A list of references (:class:`ErratumReference`) associated with the advisory."""

    pkglist = attr.ib(type=list, default=attr.Factory(frozenlist), converter=frozenlist)
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

    content_types = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """A list of content types associated with the advisory.

    For example, "docker" may be found in this list if the advisory deals
    with container images.
    """

    def __str__(self):
        return "%s: %s" % (self.name, self.title or "<untitled advisory>")

    @classmethod
    def _from_data(cls, data):
        # Helper to load an instance from the raw dicts used in various places:
        #
        # - json/yaml files in staging area
        # - output of get_advisory_cdn_metadata method in ET
        # - erratum unit metadata in Pulp2's API
        #

        kwargs = {}

        # Fill in the base push item attributes first.
        kwargs["name"] = data["id"]
        kwargs["state"] = "PENDING"

        # Now the erratum-specific fields.
        # Many are accepted verbatim from raw input; these are mandatory
        # (i.e. we'll crash if the field is missing from input).
        for field in [
            "type",
            "release",
            "status",
            "pushcount",
            "reboot_suggested",
            "rights",
            "title",
            "description",
            "version",
            "updated",
            "issued",
            "severity",
            "summary",
            "solution",
        ]:
            kwargs[field] = data[field]

        # Workaround to avoid python keyword
        kwargs["from_"] = data["from"]

        # If the metadata has a cdn_repo field, this sets the destinations for the
        # push item; used for text-only errata.
        if data.get("cdn_repo"):
            kwargs["dest"] = data["cdn_repo"]

        # If there are content type hints, copy those while dropping the
        # pulp-specific terminology
        pulp_user_metadata = data.get("pulp_user_metadata") or {}
        if pulp_user_metadata.get("content_types"):
            kwargs["content_types"] = pulp_user_metadata["content_types"]

        kwargs["references"] = ErratumReference._from_data(data.get("references") or [])

        kwargs["pkglist"] = ErratumPackageCollection._from_data(
            data.get("pkglist") or []
        )

        return cls(**kwargs)
