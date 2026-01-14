import json
import logging
import os

from ...compat_attr import attr

LOG = logging.getLogger("pushsource.konflux")


@attr.s()
class KonfluxAdvisoryData(object):
    """Stores advisory data loaded from JSON files."""

    advisory_id = attr.ib(type=str)
    metadata = attr.ib(type=dict)  # advisory_cdn_metadata content
    filelist = attr.ib(type=dict)  # advisory_cdn_filelist content


class KonfluxLoader(object):
    """Loads advisory data from local JSON files."""

    def __init__(self, base_dir):
        """Initialize loader with base directory.

        Parameters:
            base_dir (str):
                Base directory containing advisory subdirectories.
        """
        self._base_dir = base_dir

    def load_advisory_data(self, advisory_id):
        """Load both advisory_cdn_metadata and advisory_cdn_filelist.

        Parameters:
            advisory_id (str):
                Advisory ID (e.g., "RHSA-2020-0509")

        Returns:
            KonfluxAdvisoryData: Named tuple with metadata and filelist

        Raises:
            FileNotFoundError: If JSON files don't exist
            ValueError: If JSON is invalid or malformed
        """
        advisory_dir = os.path.join(self._base_dir, advisory_id)

        LOG.debug("Loading advisory data for %s from %s", advisory_id, advisory_dir)

        metadata = self._load_json(
            os.path.join(advisory_dir, "advisory_cdn_metadata.json")
        )
        filelist = self._load_json(
            os.path.join(advisory_dir, "advisory_cdn_filelist.json")
        )

        LOG.info("Successfully loaded advisory data for %s", advisory_id)

        return KonfluxAdvisoryData(
            advisory_id=advisory_id, metadata=metadata, filelist=filelist
        )

    def _load_json(self, filepath):
        """Load and parse a JSON file with error handling.

        Parameters:
            filepath (str):
                Path to JSON file to load

        Returns:
            dict: Parsed JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError("Required file not found: %s" % filepath)

        LOG.debug("Loading JSON file: %s", filepath)

        with open(filepath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON in %s: %s" % (filepath, str(e))) from e
