import logging

from more_executors import Executors

from ...source import Source
from ...model import ErratumPushItem, RpmPushItem
from ... import compat_attr as attr
from ...helpers import list_argument, as_completed_with_timeout_reset

from .konflux_loader import KonfluxLoader

LOG = logging.getLogger("pushsource.konflux")


class KonfluxSource(Source):
    """Source for push items loaded from Konflux JSON files.

    This source reads advisory metadata from local JSON files organized
    in subdirectories per advisory, and generates push items for RPMs
    and erratum metadata.

    The source is designed to be extensible and can support additional
    content types (such as modules, container images, etc.) in the future.

    Note: This source does not currently support filtering by architecture,
    though such filtering could be added if needed.
    """

    def __init__(
        self,
        url,
        advisories,
        threads=4,
        timeout=60 * 60,
    ):
        """Create a new Konflux source.

        Parameters:
            url (str):
                Base directory containing advisory subdirectories.
                Each subdirectory should be named after an advisory ID
                and contain advisory_cdn_metadata.json and
                advisory_cdn_filelist.json files.

            advisories (str, list[str]):
                Advisory ID(s) to process. Can be a single string or list.
                Multiple IDs can be comma-separated.

            threads (int):
                Number of threads for concurrent processing.

            timeout (int):
                Timeout in seconds for operations.
        """
        self._base_dir = url
        self._advisories = list_argument(advisories)
        self._threads = threads
        self._timeout = timeout

        self._loader = KonfluxLoader(url)
        self._executor = Executors.thread_pool(
            name="pushsource-konflux", max_workers=threads
        ).with_cancel_on_shutdown()

        LOG.info(
            "Initialized KonfluxSource with base_dir=%s, advisories=%s",
            url,
            self._advisories,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._executor.shutdown(True)

    def __iter__(self):
        """Yield push items for all advisories."""
        # Process advisories in parallel
        futures_list = [
            self._executor.submit(self._process_advisory, adv_id)
            for adv_id in self._advisories
        ]

        for future in as_completed_with_timeout_reset(
            futures_list, timeout=self._timeout
        ):
            # Each future returns a list of push items
            for item in future.result():
                yield item

    def _process_advisory(self, advisory_id):
        """Process a single advisory and return all its push items.

        Parameters:
            advisory_id (str):
                Advisory ID to process

        Returns:
            list[PushItem]: List of push items for this advisory
        """
        LOG.info("Processing advisory: %s", advisory_id)

        items = []

        # Load data from JSON files
        data = self._loader.load_advisory_data(advisory_id)

        # Generate erratum push item
        items.append(self._create_erratum_item(data))

        # Generate RPM push items
        items.extend(self._create_rpm_items(data))

        LOG.info("Generated %d push items for %s", len(items), advisory_id)

        return items

    def _create_erratum_item(self, data):
        """Create ErratumPushItem from advisory metadata.

        Parameters:
            data (KonfluxAdvisoryData):
                Advisory data containing metadata and filelist

        Returns:
            ErratumPushItem: Erratum push item
        """
        # advisory_cdn_metadata already has the right structure
        # Just need to ensure it has the expected fields
        metadata = data.metadata.copy()

        # Collect all destinations from RPMs
        all_destinations = set()
        for build_data in data.filelist.values():
            if "rpms" in build_data:
                for _, repos in build_data["rpms"].items():
                    all_destinations.update(repos)

        # ErratumPushItem._from_data expects metadata with cdn_repo for destinations
        metadata["cdn_repo"] = sorted(all_destinations)

        # Use the same factory method as ErrataSource
        erratum = ErratumPushItem._from_data(metadata)

        # Set origin to the advisory ID
        return attr.evolve(erratum, origin=data.advisory_id)

    def _create_rpm_items(self, data):
        """Create RpmPushItem instances from filelist data.

        Since we don't use koji, we construct RPM push items directly
        from the information in advisory_cdn_filelist.json.

        Parameters:
            data (KonfluxAdvisoryData):
                Advisory data containing metadata and filelist

        Returns:
            list[RpmPushItem]: List of RPM push items
        """
        items = []

        for build_nvr, build_data in data.filelist.items():
            if "rpms" in build_data:
                checksums = build_data.get("checksums", {})
                sig_key = build_data.get("sig_key")

                for rpm_filename, destinations in build_data["rpms"].items():
                    # Construct RPM push item
                    item = self._create_rpm_item(
                        filename=rpm_filename,
                        build_nvr=build_nvr,
                        destinations=destinations,
                        checksums=checksums,
                        signing_key=sig_key,
                        origin=data.advisory_id,
                    )
                    items.append(item)

        return items

    def _create_rpm_item(
        self, filename, build_nvr, destinations, checksums, signing_key, origin
    ):
        """Create a single RpmPushItem from filelist data.

        Parameters:
            filename (str):
                RPM filename
            build_nvr (str):
                Build NVR
            destinations (list[str]):
                List of repository destinations
            checksums (dict):
                Dict with 'md5' and 'sha256' checksum mappings
            signing_key (str):
                Signing key ID
            origin (str):
                Advisory ID

        Returns:
            RpmPushItem: RPM push item
        """
        # Extract checksums for this specific RPM
        md5sum = checksums.get("md5", {}).get(filename)
        sha256sum = checksums.get("sha256", {}).get(filename)

        return RpmPushItem(
            name=filename,
            state="PENDING",
            src=None,  # RPMs are stored in artifact storage
            dest=sorted(destinations),
            md5sum=md5sum,
            sha256sum=sha256sum,
            origin=origin,
            build=build_nvr,
            signing_key=signing_key,
        )


# Register the backend
Source.register_backend("konflux", KonfluxSource)
