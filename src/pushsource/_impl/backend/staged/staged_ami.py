import os
import logging

from ...model import AmiRelease, AmiPushItem
from .staged_base import StagedBaseMixin, handles_type

LOG = logging.getLogger("pushsource")


class StagedAmiMixin(StagedBaseMixin):
    @handles_type("AWS_IMAGES")
    def __push_item(self, leafdir, metadata, entry):
        relative_path = os.path.join(leafdir.dest, leafdir.file_type, entry.name)
        file_md = metadata.file_metadata_or_die(relative_path)
        attributes = file_md.attributes
        release_md = attributes["release"]

        release_attrs = [
            "product",
            "date",
            "arch",
            "respin",
            "version",
            "base_product",
            "base_version",
            "variant",
            "type",
        ]
        release_kwargs = {}
        for key in release_attrs:
            if key in release_md:
                release_kwargs[key] = release_md[key]

        release = AmiRelease(**release_kwargs)

        image_attrs = [
            "type",
            "region",
            "virtualization",
            "volume",
            "root_device",
            "description",
            "sriov_net_support",
            "ena_support",
        ]
        image_kwargs = {"release": release}
        for key in image_attrs:
            if key in attributes:
                image_kwargs[key] = attributes[key]

        return AmiPushItem(
            name=entry.name,
            src=entry.path,
            origin=leafdir.topdir,
            dest=[leafdir.dest],
            **image_kwargs
        )
