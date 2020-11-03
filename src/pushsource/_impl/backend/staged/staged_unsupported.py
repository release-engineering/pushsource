import logging

from .staged_base import StagedBaseMixin, handles_type

LOG = logging.getLogger("pushsource")


class StagedUnsupportedMixin(StagedBaseMixin):
    @handles_type("DOCKER")
    @handles_type("CHANNEL_DUMPS")
    def __push_item(self, _leafdir, _metadata, entry):
        LOG.error("Unsupported content found: %s", entry.path)
        return None
