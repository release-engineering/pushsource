import logging
import json
import yaml

from .staged_base import StagedBaseMixin, handles_type
from ... import compat_attr as attr
from ...model import ErratumPushItem
from ...validator import Validator

LOG = logging.getLogger("pushsource")
VALIDATOR = Validator("errata", ["filename", "id"])


class StagedErrataMixin(StagedBaseMixin):
    @handles_type("ERRATA")
    def __make_push_item(self, leafdir, _, entry):
        with open(entry.path, "rt") as fh:
            if entry.path.endswith(".json"):
                raw = json.load(fh)
            else:
                raw = yaml.safe_load(fh)

        # This field can be provided when data comes from ET,
        # but NOT when using staged files, as the staging structure
        # itself encodes the destinations.
        raw.pop("cdn_repo", None)

        VALIDATOR.validate(raw, entry.path)

        item = ErratumPushItem._from_data(raw)
        return attr.evolve(
            item, origin=leafdir.topdir, src=entry.path, dest=item.dest + [leafdir.dest]
        )
