import logging
import os
import yaml

from .staged_base import StagedBaseMixin, handles_type
from ...model import (
    VHDPushItem,
    VMIRelease,
    AmiPushItem,
    AmiRelease,
    BootMode,
    KojiBuildInfo,
)

LOG = logging.getLogger("pushsource")


class StagedCloudMixin(StagedBaseMixin):
    def __get_product_name(self, base_name):
        splitted_name = base_name.split("-")
        if len(splitted_name) > 1:
            product = "-".join(splitted_name[:-1])
        else:
            product = splitted_name[0]
        return product

    def __build_ami_push_item(self, resources, origin, image, dest):
        build_resources = resources.get("build")
        release_resources = resources.get("release") or {}
        name = image.get("path")
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
            "sha256sum": image.get("sha256sum"),
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

        release_kwargs = {
            "product": self.__get_product_name(build_resources.get("name")),
            "arch": image.get("architecture"),
            "respin": int(build_resources.get("respin")) or 0,
            "version": release_resources.get("version")
            or build_resources.get("version"),
        }
        release_attrs = [
            "date",
            "base_product",
            "base_version",
            "variant",
            "type",
        ]
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

    def __build_azure_push_item(self, resources, origin, image, dest):
        build_resources = resources.get("build")
        release_resources = resources.get("release") or {}
        name = image.get("path")
        src = os.path.join(origin, name)
        build_info = KojiBuildInfo(
            name=build_resources.get("name"),
            version=build_resources.get("version"),
            release=build_resources.get("respin"),
        )

        release_kwargs = {
            "product": self.__get_product_name(build_resources.get("name")),
            "date": release_resources.get("date"),
            "arch": image.get("architecture"),
            "respin": int(build_resources.get("respin")) or 0,
            "version": release_resources.get("version")
            or build_resources.get("version"),
        }

        image_kwargs = {
            "name": name,
            "src": src,
            "description": resources.get("description"),
            "build_info": build_info,
            "origin": origin,
            "dest": [dest],
            "sha256sum": image.get("sha256sum"),
            "release": VMIRelease(**release_kwargs),
        }
        return VHDPushItem(**image_kwargs)

    @handles_type(
        "CLOUD_IMAGES",
        accepts=lambda entry: entry.is_dir()
        and os.path.exists(os.path.join(entry.path, "resources.yaml")),
    )
    def __cloud_push_item(self, leafdir, _, entry):
        yaml_path = os.path.join(entry.path, "resources.yaml")
        with open(yaml_path, "rt") as fh:
            raw = yaml.safe_load(fh)
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
                    self.__build_ami_push_item(raw, entry.path, image, leafdir.dest)
                )
            elif image_type == "VHD":
                out.append(
                    self.__build_azure_push_item(raw, entry.path, image, leafdir.dest)
                )
        return out
