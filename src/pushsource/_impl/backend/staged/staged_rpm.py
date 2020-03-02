import logging

import kobo.rpmlib

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

        header = kobo.rpmlib.get_rpm_header(entry.path)
        key_id = kobo.rpmlib.get_keys_from_header(header)

        return RpmPushItem(
            name=entry.name,
            src=entry.path,
            signing_key=key_id,
            origin=leafdir.topdir,
            dest=[leafdir.dest],
        )
