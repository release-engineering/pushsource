import logging
import os
import yaml

from .staged_base import StagedBaseMixin, handles_type
from ...model import VHDPushItem, AmiPushItem, AmiRelease, BootMode, KojiBuildInfo

LOG = logging.getLogger("pushsource")


class StagedCloudMixin(StagedBaseMixin):
    def __build_ami_push_item(self, resources, origin, name, dest):
        build_resources = resources.get("build")
        release_resources = resources.get("release") or {}
        src = os.path.join(origin, name)
        build_info = KojiBuildInfo(
            name=build_resources.get("name"),
            version=build_resources.get("version"),
            release=build_resources.get("respin"),
        )
        image_kwargs = {
            "name": name,
            "src": src,
            "build_info": build_info,
            "origin": origin,
            "dest": [dest],
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
        if all(x in release_resources.keys() for x in release_required):
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
                release_kwargs[key] = release_resources.get(key)

            image_kwargs["release"] = AmiRelease(**release_kwargs)

        image_attrs = [
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

    def __build_azure_push_item(self, resources, origin, name, dest):
        build_resources = resources.get("build")
        src = os.path.join(origin, name)
        build_info = KojiBuildInfo(
            name=build_resources.get("name"),
            version=build_resources.get("version"),
            release=build_resources.get("respin"),
        )
        image_kwargs = {
            "name": name,
            "src": src,
            "description": resources.get("description"),
            "build_info": build_info,
            "origin": origin,
            "dest": [dest],
        }
        return VHDPushItem(**image_kwargs)

    def __process_builds(self, current_dir, leafdir):
        yaml_path = os.path.join(current_dir, "resources.yaml")
        try:
            with open(yaml_path, "rt") as fh:
                raw = yaml.safe_load(fh)
        except FileNotFoundError:
            LOG.warning("No resources.yaml file found at %s (ignored)", yaml_path)
            return
        if not raw:
            LOG.warning("Resources.yaml file at %s is empty (ignored)", yaml_path)
            return
        image_type = raw.get("type") or ""
        images_info = raw.get("images") or []
        out = []
        for image in images_info:
            if "/" in image.get("path"):
                LOG.warning("Unexpected '/' in %s (ignored)", image.get("path"))
                return
            if image_type == "AMI":
                out.append(
                    self.__build_ami_push_item(
                        raw, current_dir, image.get("path"), leafdir.dest
                    )
                )
            elif image_type == "VHD":
                out.append(
                    self.__build_azure_push_item(
                        raw, current_dir, image.get("path"), leafdir.dest
                    )
                )
        return out

    @handles_type("CLOUD_IMAGES",
                  accepts=lambda entry: entry.is_dir() and os.path.exists(os.path.join(entry.path, "resources.yaml")))
    def __cloud_push_item(self, leafdir, metadata, entry):
        out = self.__process_builds(entry.path, leafdir)

        return out
