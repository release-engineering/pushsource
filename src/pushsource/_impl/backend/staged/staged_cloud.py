import logging
import yaml
import os

from .staged_base import StagedBaseMixin, handles_type
from ...model import VHDPushItem, AmiPushItem, AmiRelease, BootMode, KojiBuildInfo

LOG = logging.getLogger("pushsource")


class StagedCloudMixin(StagedBaseMixin):
    def __build_ami_push_item(self, resources, src, origin, name):
        build_resources = resources.get("build")
        build_info = KojiBuildInfo(
            name=build_resources.get("name"),
            version=build_resources.get("version"),
            release=build_resources.get("respin")
        )
        image_kwargs = {
            "name": name,
            "src": src,
            "build_info": build_info,
            "origin": origin,
        }

        image_kwargs.update(
            {
                "boot_mode": (
                    BootMode(resources.get("boot_mode"))
                    if resources.get("boot_mode")
                    else None
                )
            }
        )

        release_required = ["product", "date", "arch", "respin"]
        if all(x in build_resources for x in release_required):
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
                release_kwargs[key] = build_resources.get(key)

            image_kwargs["release"] = AmiRelease(**release_kwargs)

        image_attrs = [
            "dest",
            "type",
            "region",
            "virtualization",
            "volume",
            "root_device",
            "description",
            "sriov_net_support",
            "ena_support",
            "uefi_support",
            "public_image",
            "release_notes",
            "usage_instructions",
            "recommended_instance_type",
            "marketplace_entity_type",
            "image_id",
            "scanning_port",
            "user_name",
            "version_title",
            "security_groups",
            "access_endpoint_url",
        ]

        for key in image_attrs:
            if key in resources:
                image_kwargs[key] = resources.get(key)

        return AmiPushItem(**image_kwargs)
    
    def __build_azure_push_item(self, resources, src, origin, name):
        build_resources = resources.get("build")
        build_info = KojiBuildInfo(
            name=build_resources.get("name"),
            version=build_resources.get("version"),
            release=build_resources.get("respin")
        )
        image_kwargs = {
            "name": name,
            "src": src,
            "build_info": build_info,
            "origin": origin,
        }
        return VHDPushItem(**image_kwargs)

    @handles_type("CLOUD_IMAGES")
    def __cloud_push_item(self, leafdir, metadata, entry):
        with open(entry.path, "rt") as fh:
            raw = yaml.safe_load(fh)
        if not raw:
            return

        out = []
        image_type = raw.get("type")
        images_info = raw.get("images")

        for image in images_info:
            image_relative_path = os.path.join(leafdir.path, image.get("path"))
            if image_type == "AMI":
                out.append(self.__build_ami_push_item(raw,
                                                      image_relative_path,
                                                      leafdir.topdir,
                                                      image.get("path")))
            elif image_type == "VHD":
                out.append(self.__build_azure_push_item(raw,
                                                        image_relative_path,
                                                        leafdir.topdir,
                                                        image.get("path")))

        return out