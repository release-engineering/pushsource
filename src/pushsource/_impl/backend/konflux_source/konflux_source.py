import logging
import os

import anyio
from more_executors import Executors

from ...source import Source
from ...model import ErratumPushItem, RpmPushItem
from ... import compat_attr as attr
from ...helpers import list_argument, as_completed_with_timeout_reset

from .konflux_loader import KonfluxLoader

from pubtools.pulplib import Pulp3Client

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
        pulp_url=None,
        pulp_cert=None,
        pulp_key=None,
        pulp_user=None,
        pulp_password=None,
        pulp_domain=None,
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

            pulp_url (str):
                URL of hosted Pulp server
                (e.g., https://packages.redhat.com/).
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_URL``
                environment variable.

            pulp_cert (str):
                Path to TLS client certificate for Pulp authentication.
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_CERT``
                environment variable.

            pulp_key (str):
                Path to TLS client key for Pulp authentication.
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_KEY``
                environment variable.

            pulp_user (str):
                Username for Pulp basic authentication.
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_USER``
                environment variable. Use with ``pulp_password``
                as an alternative to certificate authentication.

            pulp_password (str):
                Password for Pulp basic authentication.
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_PASSWORD``
                environment variable.

            pulp_domain (str):
                Pulp domain name (e.g., "konflux-myteam-tenant").
                If omitted, uses ``PUSHSOURCE_KONFLUX_PULP_DOMAIN``
                environment variable.

            threads (int):
                Number of threads for concurrent processing.

            timeout (int):
                Timeout in seconds for operations.
        """
        self._base_dir = url
        self._threads = threads
        self._timeout = timeout

        self._loader = KonfluxLoader(url)

        self._advisories = list_argument(advisories)

        # Resolve Pulp params from env vars if not provided
        pulp_url = pulp_url or os.environ.get("PUSHSOURCE_KONFLUX_PULP_URL")
        pulp_cert = pulp_cert or os.environ.get("PUSHSOURCE_KONFLUX_PULP_CERT")
        pulp_key = pulp_key or os.environ.get("PUSHSOURCE_KONFLUX_PULP_KEY")
        pulp_user = pulp_user or os.environ.get("PUSHSOURCE_KONFLUX_PULP_USER")
        pulp_password = pulp_password or os.environ.get(
            "PUSHSOURCE_KONFLUX_PULP_PASSWORD"
        )
        pulp_domain = pulp_domain or os.environ.get("PUSHSOURCE_KONFLUX_PULP_DOMAIN")

        # Validate required params
        if not pulp_url:
            raise RuntimeError("Required parameter not provided: pulp_url")
        if not pulp_domain:
            raise RuntimeError("Required parameter not provided: pulp_domain")

        # Validate that at least one auth method is provided
        has_cert_auth = pulp_cert and pulp_key
        has_basic_auth = pulp_user and pulp_password
        if not has_cert_auth and not has_basic_auth:
            raise RuntimeError(
                "Pulp authentication not configured. Provide either "
                "pulp_cert/pulp_key for mTLS or pulp_user/pulp_password "
                "for basic authentication."
            )

        LOG.info(
            "Initializing Pulp3 client: url=%s, domain=%s, auth=%s",
            pulp_url,
            pulp_domain,
            "cert" if has_cert_auth else "basic",
        )

        # Build Pulp3Client kwargs
        self._pulp_client_kwargs = {
            "url": pulp_url,
            "domain": pulp_domain,
        }
        if has_cert_auth:
            self._pulp_client_kwargs["cert"] = (pulp_cert, pulp_key)
        elif has_basic_auth:
            self._pulp_client_kwargs["auth"] = (pulp_user, pulp_password)

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

        Collects all RPM SHA256 checksums and resolves their pulp_hrefs
        in a single batch query, then builds the push items.

        Parameters:
            data (KonfluxAdvisoryData):
                Advisory data containing metadata and filelist

        Returns:
            list[RpmPushItem]: List of RPM push items
        """
        # First pass: collect all RPM info and SHA256 checksums
        rpm_entries = []
        all_sha256s = []

        for build_nvr, build_data in data.filelist.items():
            if "rpms" not in build_data:
                continue
            checksums = build_data.get("checksums", {})
            sig_key = build_data.get("sig_key")

            for rpm_filename, destinations in build_data["rpms"].items():
                md5sum = checksums.get("md5", {}).get(rpm_filename)
                sha256sum = checksums.get("sha256", {}).get(rpm_filename)

                if not sha256sum:
                    raise RuntimeError(
                        "No SHA256 checksum found for RPM %s in advisory %s"
                        % (rpm_filename, data.advisory_id)
                    )

                all_sha256s.append(sha256sum)
                rpm_entries.append(
                    {
                        "filename": rpm_filename,
                        "build_nvr": build_nvr,
                        "destinations": destinations,
                        "md5sum": md5sum,
                        "sha256sum": sha256sum,
                        "signing_key": sig_key,
                    }
                )

        # Batch-resolve all SHA256 checksums to pulp_hrefs
        href_map = anyio.run(self._resolve_rpm_hrefs, all_sha256s)

        # Second pass: build push items using resolved hrefs
        items = []
        for entry in rpm_entries:
            sha256sum = entry["sha256sum"]
            pulp_href = href_map.get(sha256sum)
            if not pulp_href:
                raise RuntimeError(
                    "RPM %s (sha256=%s) not found in Pulp"
                    % (entry["filename"], sha256sum)
                )

            items.append(
                RpmPushItem(
                    name=entry["filename"],
                    state="PENDING",
                    src=pulp_href,
                    dest=sorted(entry["destinations"]),
                    md5sum=entry["md5sum"],
                    sha256sum=sha256sum,
                    origin=data.advisory_id,
                    build=entry["build_nvr"],
                    signing_key=entry["signing_key"],
                )
            )

        return items

    # Pulp's content search API enforces a filter complexity limit,
    # rejecting queries with more than 7 OR clauses with:
    #   {"q": ["Filter expression exceeds allowed complexity."]}
    _PULP_BATCH_SIZE = 7

    async def _resolve_rpm_hrefs(self, sha256sums, batch_size=_PULP_BATCH_SIZE):
        """Resolve SHA256 checksums to pulp_hrefs in batched queries.

        Uses one Pulp3Client instance and queries checksums in batches
        to stay within Pulp's filter complexity limits.

        Parameters:
            sha256sums (list[str]):
                List of SHA256 checksums to resolve

            batch_size (int):
                Maximum number of checksums per query (default: 7)

        Returns:
            dict: Mapping of sha256 -> pulp_href

        Raises:
            RuntimeError: If any RPM is not found or has no pulp_href
        """
        href_map = {}

        async with Pulp3Client(**self._pulp_client_kwargs) as client:
            for i in range(0, len(sha256sums), batch_size):
                batch = sha256sums[i : i + batch_size]
                query = client.build_query_sha256(batch)

                results = await client.search_content(
                    query=query,
                    fields=["pulp_href", "name", "sha256"],
                    limit=len(batch),
                )

                for result in results:
                    sha256 = result.get("sha256")
                    pulp_href = result.get("pulp_href")
                    if not pulp_href:
                        raise RuntimeError(
                            "RPM with SHA256 %s found but has no pulp_href: %s"
                            % (sha256, result)
                        )
                    href_map[sha256] = pulp_href
                    LOG.debug(
                        "Found RPM in Pulp: sha256=%s, pulp_href=%s, name=%s",
                        sha256,
                        pulp_href,
                        result.get("name"),
                    )

                LOG.info(
                    "Resolved %d/%d RPMs in Pulp (batch %d)",
                    len(href_map),
                    len(sha256sums),
                    (i // batch_size) + 1,
                )

        return href_map


# Register the backend
Source.register_backend("konflux", KonfluxSource)
