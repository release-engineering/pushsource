import logging
import os

from .staged_base import StagedBaseMixin, handles_type

from ...model import ChannelDumpPushItem

LOG = logging.getLogger("pushsource")


class StagedChannelDumpsMixin(StagedBaseMixin):
    @handles_type("CHANNEL_DUMPS")
    def __make_push_item(self, leafdir, metadata, entry):
        relative_path = os.path.join(leafdir.dest, leafdir.file_type, entry.name)
        file_md = metadata.file_metadata_or_die(relative_path)
        attributes = file_md.attributes

        # Attributes in metadata file for channel dumps,
        # all of which are mandatory.
        attribute_map = {
            "allowed_eng_products": "eng_product_ids",
            "channel_dump_arch": "arch",
            "channel_dump_content": "content",
            "channel_dump_date": "datetime",
            "channel_dump_disc_number": "disk_number",
            "channel_dump_product_name": "product_name",
            "channel_dump_product_version": "product_version",
            "channel_dump_type": "type",
            "channel_dump_included_channels": "channels",
            "description": "description",
        }

        kwargs = {}
        for key in attribute_map:
            if key not in attributes:
                raise ValueError(
                    "%s is missing mandatory attribute '%s' for %s"
                    % (metadata.filename, key, relative_path)
                )

            kwargs[attribute_map[key]] = attributes[key]

        # Any fields loaded from attributes above should be converted
        # & validated during the constructor here.
        return ChannelDumpPushItem(
            name=file_md.filename or entry.name,
            src=entry.path,
            sha256sum=file_md.sha256sum,
            origin=leafdir.topdir,
            dest=[leafdir.dest],
            **kwargs
        )
