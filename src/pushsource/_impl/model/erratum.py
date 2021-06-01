from frozenlist2 import frozenlist

from .base import PushItem
from .. import compat_attr as attr
from .conv import (
    in_,
    int2str,
    md5str,
    sha1str,
    sha256str,
    instance_of,
    instance_of_str,
    optional,
    optional_str,
)
from .erratum_fixup import fixup_erratum_class


@attr.s()
class ErratumReference(object):
    """A reference within a :meth:`~ErratumPushItem.references` list."""

    href = attr.ib(type=str, validator=instance_of_str)
    """A URL."""

    id = attr.ib(type=str, converter=int2str, validator=optional_str)
    """A short ID for the reference, unique within this erratum."""

    title = attr.ib(type=str, validator=optional_str)
    """A title for the reference; analogous to the 'title' attribute
    in HTML.
    """

    type = attr.ib(type=str, default="other", validator=instance_of_str)
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

    name = attr.ib(type=str, validator=instance_of_str)
    """Module name."""

    stream = attr.ib(type=str, validator=instance_of_str)
    """Module stream."""

    version = attr.ib(type=str, validator=instance_of_str)
    """Module version."""

    context = attr.ib(type=str, validator=instance_of_str)
    """Module context."""

    arch = attr.ib(type=str, validator=instance_of_str)
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

    arch = attr.ib(type=str, validator=instance_of_str)
    """RPM architecture."""

    filename = attr.ib(type=str, validator=instance_of_str)
    """RPM filename (basename)."""

    epoch = attr.ib(type=str, converter=int2str, validator=instance_of_str)
    """RPM epoch."""

    name = attr.ib(type=str, validator=instance_of_str)
    """RPM name (e.g. "bash-4.0.1-1.el7.x86_64.rpm" name is "bash")"""

    version = attr.ib(type=str, validator=instance_of_str)
    """RPM version (e.g. "bash-4.0.1-1.el7.x86_64.rpm" version is "4.0.1")"""

    release = attr.ib(type=str, validator=instance_of_str)
    """RPM release (e.g. "bash-4.0.1-1.el7.x86_64.rpm" version is "1.el7")"""

    src = attr.ib(type=str, validator=instance_of_str)
    """Filename of the source RPM from which this RPM was built; equal to
    :meth:`filename` for the source RPM itself.
    """

    reboot_suggested = attr.ib(type=bool, default=False, validator=instance_of(bool))
    """True if rebooting host machine is recommended after installing this package."""

    md5sum = attr.ib(type=str, default=None, converter=md5str)
    """MD5 checksum of this RPM in hex string form, if available."""

    sha1sum = attr.ib(type=str, default=None, converter=sha1str)
    """SHA1 checksum of this RPM in hex string form, if available."""

    sha256sum = attr.ib(type=str, default=None, converter=sha256str)
    """SHA256 checksum of this RPM in hex string form, if available."""


@attr.s()
class ErratumPackageCollection(object):
    """A collection of packages found within an :meth:`~ErratumPushItem.pkglist`.

    A non-modular advisory typically contains only a single collection, while modular
    advisories typically contain one collection per module.
    """

    name = attr.ib(type=str, default="", validator=instance_of_str)
    """A name for this collection. The collection name has no specific meaning,
    but must be unique within an advisory.
    """

    packages = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """List of packages within this collection.

    :type: list[ErratumPackage]
    """

    short = attr.ib(type=str, default="", validator=instance_of_str)
    """An alternative name for this collection. In practice, this field
    is typically blank.
    """

    module = attr.ib(
        type=ErratumModule, default=None, validator=optional(instance_of(ErratumModule))
    )
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
                    reboot_suggested=raw_pkg.get("reboot_suggested") or False,
                    md5sum=sums.get("md5"),
                    sha1sum=sums.get("sha1"),
                    sha256sum=sums.get("sha256"),
                )
            )

        return cls(
            name=data.get("name") or "",
            short=data.get("short") or "",
            packages=packages,
            module=ErratumModule._from_data(data.get("module")),
        )


def errata_type_converter(value):
    # For 'type' field, ancient versions of Errata Tool produced values
    # like RHBA, RHEA, RHSA, so these can be found in the wild; but all
    # other sources (including our own model) prefer strings like "bugfix".
    # We'll convert up from legacy values automatically.
    typemap = {"RHBA": "bugfix", "RHEA": "enhancement", "RHSA": "security"}
    return typemap.get(value, value)


@attr.s()
class ErratumPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a single erratum (also known as "advisory").

    Note that many fields on erratum objects which appear to be numeric
    are instead represented as strings ('release' and 'pushcount' being two
    examples).
    """

    type = attr.ib(
        type=str,
        default="bugfix",
        validator=in_(["bugfix", "security", "enhancement"]),
        converter=errata_type_converter,
    )
    """'bugfix', 'security' or 'enhancement'."""

    release = attr.ib(
        type=str, default="0", converter=int2str, validator=instance_of_str
    )
    """Release number. Typically an integer-string, initially '0'."""

    status = attr.ib(type=str, default="final", validator=instance_of_str)
    """Status, typically 'final'."""

    pushcount = attr.ib(
        type=str, default="1", converter=int2str, validator=instance_of_str
    )
    """Number of times advisory has been revised and published (starting at '1')."""

    reboot_suggested = attr.ib(type=bool, default=False, validator=instance_of(bool))
    """True if rebooting host machine is recommended after installing this advisory.

    .. warning::
        The intended usage of this field is unclear.

        In practice, tools such as yum are instead consuming the ``reboot_suggested`` field
        from :class:`ErratumPackage`.
    """

    references = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """A list of references associated with the advisory.

    :type: list[ErratumReference]
    """

    pkglist = attr.ib(type=list, default=attr.Factory(frozenlist), converter=frozenlist)
    """A list of package collections associated with the advisory.

    :type: list[ErratumPackageCollection]
    """

    from_ = attr.ib(type=str, default=None, validator=optional_str)
    """Contact email address for the owner of the advisory.

    Note that the canonical name for this attribute is ``from``. As this clashes
    with a Python keyword, in most contexts the attribute is also available as an
    alias, ``from_``. Where possible, the canonical name ``from`` should be preferred.

    :type: str
    """

    rights = attr.ib(type=str, default=None, validator=optional_str)
    """Copyright message."""

    title = attr.ib(type=str, default=None, validator=optional_str)
    """Title of the advisory (e.g. 'bash bugfix and enhancement')."""

    description = attr.ib(type=str, default=None, validator=optional_str)
    """Full human-readable description of the advisory, usually multiple lines."""

    version = attr.ib(
        type=str, default="1", converter=int2str, validator=instance_of_str
    )
    """Advisory version. Starts counting at "1", and some systems require updating
    the version whenever an advisory is modified.
    """

    updated = attr.ib(type=str, default=None, validator=optional_str)
    """Timestamp of the last update to this advisory.

    Typically of the form '2019-12-31 06:54:41 UTC', but this is not enforced.
    """

    issued = attr.ib(type=str, default=None, validator=optional_str)
    """Timestamp of the initial release of this advisory.

    Uses the same format as :meth:`updated`.
    """

    severity = attr.ib(type=str, default=None, validator=optional_str)
    """Severity of the advisory, e.g. "low", "moderate", "important" or "critical"."""

    summary = attr.ib(type=str, default=None, validator=optional_str)
    """Typically a single sentence briefly describing the advisory."""

    solution = attr.ib(type=str, default=None, validator=optional_str)
    """Text explaining how to apply the advisory."""

    content_types = attr.ib(
        type=list, default=attr.Factory(frozenlist), converter=frozenlist
    )
    """A list of content types associated with the advisory.

    For example, "docker" may be found in this list if the advisory deals
    with container images.

    :type: list[str]
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
            "from",
            "description",
            "version",
            "updated",
            "issued",
            "severity",
            "summary",
            "solution",
        ]:
            kwargs[field] = data[field]

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


# Apply from vs from_ workarounds.
fixup_erratum_class(ErratumPushItem)
