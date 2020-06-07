import logging
import json
import yaml
import jsonschema

from .staged_base import StagedBaseMixin, handles_type
from ... import compat_attr as attr
from ...model import ErratumPushItem
from ...schema import get_schema

LOG = logging.getLogger("pushsource")
ERRATA_SCHEMA = get_schema("errata")


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

        jsonschema.validate(raw, ERRATA_SCHEMA)

        item = ErratumPushItem._from_data(raw)
        return attr.evolve(
            item, origin=leafdir.topdir, src=entry.path, dest=item.dest + [leafdir.dest]
        )
