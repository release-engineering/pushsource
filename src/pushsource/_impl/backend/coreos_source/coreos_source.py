from concurrent import futures

from datetime import datetime, timezone
from more_executors import Executors

from ...source import Source
from ...helpers import (
    force_https,
    as_completed_with_timeout_reset,
    list_argument,
    try_int,
)
from ...model import AmiPushItem, VHDPushItem, KojiBuildInfo
from .coreos_client import CoreOSClient


class CoreOSSource(Source):
    """Source for VMI push items loaded from CoreOS installer file (JSON)."""

    def __init__(
        self,
        url,
        paths,
        threads=4,
        timeout=60 * 60,
    ):
        """Create a new source.

        Parameters:
            url (str)
                Base URL of for the GitHub repository containing the CoreOS installer information.
                It should contain as well the tag or branch name of the repository.
                Eg.: https://github.com/openshift/installer/tree/master
            paths (list[str])
                List of paths to the JSON files containing the CoreOS installer information.
                Eg.: ["data/data/coreos/rhcos.json", "data/data/coreos/rhcos-rhel-10.json"]
            threads (int)
                Number of threads used for concurrent queries to the CoreOS installer file.
            timeout (int)
                Number of seconds after which an error is raised, if no progress is
                made during queries to the CoreOS installer file.
        """
        self._executor = Executors.thread_pool(
            name="pushsource-coreos", max_workers=threads
        ).with_cancel_on_shutdown()
        self._url = force_https(url)
        self._client = CoreOSClient(url=self._url, threads=threads)
        self._paths = list_argument(paths)
        self._timeout = timeout

    def _push_items_from_json(self, json_obj):
        product_stream = json_obj.get("stream") or ""
        product_metadata = json_obj.get("metadata") or {}
        # Get the product name and version from the stream
        name, version = (
            product_stream.split("-") if product_stream else ("unknown", "unknown")
        )

        # Get the release date from the metadata
        release_date = product_metadata.get("last-modified") or ""
        if release_date:
            release_date = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ")
        else:
            release_date = datetime.now(timezone.utc)
        out = []
        vms_with_custom_meta_data = []
        architectures = json_obj.get("architectures") or {}
        for arch, arch_data in architectures.items():
            images = arch_data.get("images") or {}
            for cloud_name, image_data in images.items():
                if cloud_name == "aws":
                    # For AWS each region has a different AMI
                    regions = image_data.get("regions") or {}
                    for region, region_data in regions.items():
                        vms_with_custom_meta_data.append(
                            {
                                "marketplace_name": "aws",
                                "push_item_class": AmiPushItem,
                                "architecture": arch,
                                "release": region_data.get("release"),
                                "custom_meta_data": {
                                    "region": region,
                                    "src": region_data.get("image"),
                                },
                            }
                        )
            # Azure images are generally in the "rhel-coreos-extensions" section
            extensions = arch_data.get("rhel-coreos-extensions") or {}
            for extension, extension_data in extensions.items():
                if extension == "azure-disk":
                    vms_with_custom_meta_data.append(
                        {
                            "marketplace_name": "azure",
                            "architecture": arch,
                            "push_item_class": VHDPushItem,
                            "release": extension_data.get("release"),
                            "custom_meta_data": {
                                "src": extension_data.get("url"),
                            },
                        }
                    )

        for vm_item in vms_with_custom_meta_data:
            klass = vm_item.get("push_item_class")
            rel_klass = klass._RELEASE_TYPE
            vm_release = vm_item.get("release") or ""
            vm_respin = try_int(vm_release.split("-")[-1]) or 0
            release = rel_klass(
                arch=vm_item.get("architecture"),
                date=release_date,
                product=name.upper(),
                version=version,
                respin=vm_respin,
            )
            out.append(
                klass(
                    name=name,
                    description=f"CoreOS image for {name} {version} on {vm_item['marketplace_name']}",
                    **vm_item["custom_meta_data"],
                    build_info=KojiBuildInfo(
                        name=name,
                        version=version,
                        release=vm_release,
                    ),
                    release=release,
                    marketplace_name=vm_item["marketplace_name"],
                )
            )

        return out

    def __iter__(self):
        # Get all json files from the paths
        json_fs = [self._client.get_json_f(path) for path in self._paths]

        # Convert them to lists of push items
        push_items_fs = []
        for f in futures.as_completed(json_fs, timeout=self._timeout):
            push_items_fs.append(
                self._executor.submit(self._push_items_from_json, f.result())
            )

        completed_fs = as_completed_with_timeout_reset(
            push_items_fs, timeout=self._timeout
        )
        for f in completed_fs:
            for pushitem in f.result():
                yield pushitem


Source.register_backend("coreos", CoreOSSource)
