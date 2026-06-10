from datetime import datetime, timezone

import pytest

from pushsource._impl.backend.coreos_source.coreos_source import CoreOSSource
from pushsource._impl.model import AmiPushItem, VHDPushItem
from pushsource._impl.model.ami import AmiRelease
from pushsource._impl.model.vms import VMIRelease
from pushsource._impl.source import Source


class TestCoreOSSource:
    @pytest.fixture
    def coreos_source(self, mock_coreos_client):
        source = CoreOSSource(
            url="https://github.com/openshift/installer/tree/master",
            paths=["data/coreos-rhel-9.json"],
        )
        source._client = mock_coreos_client
        return source

    @pytest.fixture
    def coreos_source_with_paths(self, mock_coreos_client, request):
        source = CoreOSSource(
            url="https://github.com/openshift/installer/tree/master",
            paths=request.param,
        )
        source._client = mock_coreos_client
        return source

    def test_push_items_from_json_rhel9(self, requests_mock, coreos_rhel_9_data):
        test_url_base = "https://github.com/openshift/installer/tree/master"
        test_url_raw = "https://raw.githubusercontent.com/openshift/installer/master"
        test_path = "data/coreos-rhel-9.json"

        # Mock the request to the raw JSON file
        requests_mock.get(f"{test_url_raw}/{test_path}", json=coreos_rhel_9_data)

        # Get the source and iterate through push items
        with Source.get("coreos:%s" % test_url_base, paths=[test_path]) as source:
            push_items = [item for item in source]

        assert requests_mock.called

        assert len(push_items) == 70

        # Test AWS AMI Push Item
        aws_ami_item = next(
            (
                item
                for item in push_items
                if isinstance(item, AmiPushItem)
                and item.marketplace_name == "aws"
                and item.release.arch == "aarch64"
            ),
            None,
        )
        assert aws_ami_item is not None
        assert aws_ami_item.name == "rhcos"
        assert aws_ami_item.description.startswith("CoreOS image for rhcos 4.21 on aws")
        assert aws_ami_item.region == "af-south-1"
        assert aws_ami_item.src == "ami-09b3b126662fe7a18"
        assert isinstance(aws_ami_item.release, AmiRelease)
        assert aws_ami_item.release.arch == "aarch64"
        assert aws_ami_item.release.product == "RHCOS"
        assert aws_ami_item.release.version == "4.21"
        assert aws_ami_item.release.respin == 0
        assert aws_ami_item.release.date == datetime(2026, 5, 26, 2, 1, 1)

    def test_push_items_from_json_missing_data(
        self, requests_mock, coreos_missing_data
    ):
        test_url_base = "https://github.com/openshift/installer/tree/master"
        test_url_raw = "https://raw.githubusercontent.com/openshift/installer/master"
        test_path = "data/coreos-missing-data.json"

        # Mock the request to the raw JSON file
        requests_mock.get(f"{test_url_raw}/{test_path}", json=coreos_missing_data)

        # Get the source and iterate through push items
        with Source.get("coreos:%s" % test_url_base, paths=[test_path]) as source:
            push_items = [item for item in source]

        assert requests_mock.called

        # Expected behavior for missing stream/metadata: name, version will be empty, date will be current date
        assert len(push_items) == 2

        # Test AWS AMI Push Item with missing data
        aws_ami_item = next(
            (
                item
                for item in push_items
                if isinstance(item, AmiPushItem)
                and item.marketplace_name == "aws"
                and item.release.arch == "aarch64"
            ),
            None,
        )
        assert aws_ami_item is not None
        assert aws_ami_item.name == "unknown"
        assert aws_ami_item.description.startswith(
            "CoreOS image for unknown unknown on aws"
        )
        assert aws_ami_item.region == "af-south-1"
        assert aws_ami_item.src == "ami-09b3b126662fe7a18"
        assert isinstance(aws_ami_item.release, AmiRelease)
        assert aws_ami_item.release.arch == "aarch64"
        assert aws_ami_item.release.product == "UNKNOWN"
        assert aws_ami_item.release.version == "unknown"
        assert aws_ami_item.release.respin == 0
        assert isinstance(aws_ami_item.release.date, datetime)
        assert aws_ami_item.release.date.tzinfo == timezone.utc

        # Test Azure VHD Push Item with missing data
        azure_vhd_item = next(
            (
                item
                for item in push_items
                if isinstance(item, VHDPushItem)
                and item.marketplace_name == "azure"
                and item.release.arch == "aarch64"
            ),
            None,
        )
        assert azure_vhd_item is not None
        assert azure_vhd_item.name == "unknown"
        assert azure_vhd_item.description.startswith(
            "CoreOS image for unknown unknown on azure"
        )
        assert (
            azure_vhd_item.src
            == "https://rhcos.blob.core.windows.net/imagebucket/rhcos-9.8.20260520-0-azure.aarch64.vhd"
        )
        assert isinstance(azure_vhd_item.release, VMIRelease)
        assert azure_vhd_item.release.arch == "aarch64"
        assert azure_vhd_item.release.product == "UNKNOWN"
        assert azure_vhd_item.release.version == "unknown"
        assert azure_vhd_item.release.respin == 0
        assert isinstance(azure_vhd_item.release.date, datetime)
        assert azure_vhd_item.release.date.tzinfo == timezone.utc
