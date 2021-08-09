import logging

try:
    from kobo import rpmlib
except Exception as ex:  # pragma: no cover, pylint: disable=broad-except
    # If kobo.rpmlib is unavailable, let's not immediately crash.
    # We will hold this exception and re-raise it only if there's an
    # attempt to use the related functionality.
    from .. import broken_rpmlib as rpmlib

    rpmlib.CAUSE = ex

from ...model import RpmPushItem
from .staged_base import StagedBaseMixin, handles_type

LOG = logging.getLogger("pushsource")


class StagedRpmMixin(StagedBaseMixin):
    @handles_type("RPMS")
    @handles_type("SRPMS")
    def __push_item(self, leafdir, _, entry):
        if not entry.name.endswith(".rpm"):
            # Old code accepted (ignored) non-RPMs in RPMs dir.
            # It's not clear how widespread this is, so we'd better tolerate it,
            # but we don't like it, so let's warn.
            LOG.warning("Unexpected non-RPM %s (ignored)", entry.path)
            return None

        header = rpmlib.get_rpm_header(entry.path)
        key_id = rpmlib.get_keys_from_header(header)

        return RpmPushItem(
            name=entry.name,
            src=entry.path,
            signing_key=key_id,
            origin=leafdir.topdir,
            dest=[leafdir.dest],
        )
