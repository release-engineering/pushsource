import os
import pytest
import tempfile
import json
from unittest.mock import AsyncMock, MagicMock, patch

import anyio

from pushsource import Source
from pushsource._impl.backend.konflux_source import KonfluxSource
from pushsource._impl.model import (
    ErratumPushItem,
    ErratumPackage,
    ErratumPackageCollection,
    ErratumReference,
    RpmPushItem,
)

DATADIR = os.path.join(os.path.dirname(__file__), "data")

# Default Pulp connection params for tests
PULP_PARAMS = {
    "pulp_url": "https://pulp.example.com",
    "pulp_cert": "/path/to/cert",
    "pulp_key": "/path/to/key",
    "pulp_domain": "konflux-myteam-tenant",
}


def _mock_resolve_hrefs(func, sha256sums):
    """Mock for anyio.run that returns a dict mapping each sha256 to a mock href."""
    return {
        sha256: "/pulp/api/v3/content/rpm/packages/mock-uuid/" for sha256 in sha256sums
    }


def test_load_single_advisory():
    """Test loading a single advisory and generating push items."""
    url = (
        "konflux:%s?"
        "pulp_url=https://pulp.example.com"
        "&pulp_cert=/path/to/cert"
        "&pulp_key=/path/to/key"
        "&pulp_domain=konflux-myteam-tenant"
        "&advisories=RHSA-2020:0509"
    ) % DATADIR
    mock_href = "/pulp/api/v3/content/rpm/packages/mock-uuid/"
    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.anyio.run",
        side_effect=_mock_resolve_hrefs,
    ):
        with Source.get(url) as source:
            items = list(source)

    # Should have 1 erratum + 7 RPMs
    assert len(items) == 8

    erratum_items = [i for i in items if isinstance(i, ErratumPushItem)]
    rpm_items = [i for i in items if isinstance(i, RpmPushItem)]

    # Should have exactly one erratum
    assert len(erratum_items) == 1
    erratum = erratum_items[0]

    # Should have 7 RPMs total
    assert len(rpm_items) == 7

    # Validate erratum string representation
    assert str(erratum) == "RHSA-2020:0509: Important: sudo security update"

    # Validate basic erratum fields
    assert erratum.name == "RHSA-2020:0509"
    assert erratum.origin == "RHSA-2020:0509"
    assert erratum.severity == "Important"

    # Validate pkglist structure with complete object comparison
    assert erratum.pkglist == [
        ErratumPackageCollection(
            name="",
            packages=[
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="0d56f302617696d3511e71e1669e62c0",
                    sha1sum=None,
                    sha256sum="31c4f73af90c6d267cc5281c59e4a93ae3557b2253d9a8e3fef55f3cafca6e54",
                ),
                ErratumPackage(
                    arch="SRPMS",
                    filename="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="f94ab3724b498e3faeab643fe2a67c9c",
                    sha1sum=None,
                    sha256sum="10d7724302a60d0d2ca890fc7834b8143df55ba1ce0176469ea634ac4ab7aa28",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="25e9470c4fe96034fe1d7525c04b5d8e",
                    sha1sum=None,
                    sha256sum="593f872c1869f7beb963c8df2945fc691a1d999945c8c45c6bc7e02731fa016f",
                ),
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo-debuginfo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="e242826fb38f487502cdc1f1a06991d2",
                    sha1sum=None,
                    sha256sum="04db0c39efb31518ff79bf98d1c27256d46cdc72b967a5b2094a6efec3166df2",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo-debuginfo",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="91126f02975c06015880d6ea99cb2760",
                    sha1sum=None,
                    sha256sum="1b7d3a7613236ffea7c4553eb9dea69fc19557005ac3a059d7e83efc08c5b754",
                ),
                ErratumPackage(
                    arch="ppc64le",
                    filename="sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                    epoch="0",
                    name="sudo-debugsource",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    reboot_suggested=True,
                    md5sum="d6da7e2e3d9efe050fef2e8d047682be",
                    sha1sum=None,
                    sha256sum="355cbb9dc348b17782cff57120391685d6a1f6884facc54fac4b7fb54abeffba",
                ),
                ErratumPackage(
                    arch="x86_64",
                    filename="sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm",
                    epoch="0",
                    name="sudo-debugsource",
                    version="1.8.25p1",
                    release="4.el8_0.3",
                    src="sudo-1.8.25p1-4.el8_0.3.src.rpm",
                    md5sum="6b0967941c0caf626c073dc7da0272b6",
                    sha1sum=None,
                    sha256sum="43e318fa49e4df685ea0d5f0925a00a336236b2e20f27f9365c39a48102c2cf6",
                ),
            ],
            short="",
            module=None,
        )
    ]

    # Erratum destinations should match all unique RPM destinations
    rpm_dests = []
    for rpm in rpm_items:
        # Each RPM should be shipped to at least one repository
        assert len(rpm.dest) >= 1
        rpm_dests.extend(rpm.dest)
    assert set(erratum.dest) == set(rpm_dests)

    # Validate all RPM items with complete object comparison
    assert sorted(rpm_items, key=lambda rpm: rpm.name) == [
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-ppc64le-baseos-rpms__8",
                "rhel-8-for-ppc64le-baseos-rpms__8_DOT_0",
            ],
            md5sum="0d56f302617696d3511e71e1669e62c0",
            sha256sum="31c4f73af90c6d267cc5281c59e4a93ae3557b2253d9a8e3fef55f3cafca6e54",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.src.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-ppc64le-baseos-source-rpms__8",
                "rhel-8-for-ppc64le-baseos-source-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-e4s-source-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-source-rpms__8",
                "rhel-8-for-x86_64-baseos-source-rpms__8_DOT_0",
            ],
            md5sum="f94ab3724b498e3faeab643fe2a67c9c",
            sha256sum="10d7724302a60d0d2ca890fc7834b8143df55ba1ce0176469ea634ac4ab7aa28",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-x86_64-baseos-e4s-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-rpms__8",
                "rhel-8-for-x86_64-baseos-rpms__8_DOT_0",
            ],
            md5sum="25e9470c4fe96034fe1d7525c04b5d8e",
            sha256sum="593f872c1869f7beb963c8df2945fc691a1d999945c8c45c6bc7e02731fa016f",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-ppc64le-baseos-debug-rpms__8",
                "rhel-8-for-ppc64le-baseos-debug-rpms__8_DOT_0",
            ],
            md5sum="e242826fb38f487502cdc1f1a06991d2",
            sha256sum="04db0c39efb31518ff79bf98d1c27256d46cdc72b967a5b2094a6efec3166df2",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-x86_64-baseos-debug-rpms__8",
                "rhel-8-for-x86_64-baseos-debug-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-e4s-debug-rpms__8_DOT_0",
            ],
            md5sum="91126f02975c06015880d6ea99cb2760",
            sha256sum="1b7d3a7613236ffea7c4553eb9dea69fc19557005ac3a059d7e83efc08c5b754",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-ppc64le-baseos-debug-rpms__8",
                "rhel-8-for-ppc64le-baseos-debug-rpms__8_DOT_0",
            ],
            md5sum="d6da7e2e3d9efe050fef2e8d047682be",
            sha256sum="355cbb9dc348b17782cff57120391685d6a1f6884facc54fac4b7fb54abeffba",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
        RpmPushItem(
            name="sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm",
            state="PENDING",
            src=mock_href,
            dest=[
                "rhel-8-for-x86_64-baseos-debug-rpms__8",
                "rhel-8-for-x86_64-baseos-debug-rpms__8_DOT_0",
                "rhel-8-for-x86_64-baseos-e4s-debug-rpms__8_DOT_0",
            ],
            md5sum="6b0967941c0caf626c073dc7da0272b6",
            sha256sum="43e318fa49e4df685ea0d5f0925a00a336236b2e20f27f9365c39a48102c2cf6",
            origin="RHSA-2020:0509",
            build="sudo-1.8.25p1-4.el8_0.3",
            signing_key="FD431D51",
        ),
    ]


def test_load_comma_separated_advisories():
    """Test loading advisories specified as a comma-separated string."""
    url = (
        "konflux:%s?"
        "pulp_url=https://pulp.example.com"
        "&pulp_cert=/path/to/cert"
        "&pulp_key=/path/to/key"
        "&pulp_domain=konflux-myteam-tenant"
        "&advisories=RHSA-2020:0509,RHBA-2020:1234"
    ) % DATADIR
    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.anyio.run",
        side_effect=_mock_resolve_hrefs,
    ):
        with Source.get(url) as source:
            items = list(source)

    erratum_items = [i for i in items if isinstance(i, ErratumPushItem)]
    rpm_items = [i for i in items if isinstance(i, RpmPushItem)]

    # Should have both advisories
    assert len(erratum_items) == 2
    advisory_ids = sorted(e.name for e in erratum_items)
    assert advisory_ids == ["RHBA-2020:1234", "RHSA-2020:0509"]

    # Should have 7 RPMs from RHSA-2020:0509 + 1 RPM from RHBA-2020:1234
    assert len(rpm_items) == 8


def test_invalid_json():
    """Test error handling for invalid JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create advisory directory
        adv_dir = os.path.join(tmpdir, "TEST-2020:0001")
        os.makedirs(adv_dir)

        # Create invalid JSON file
        with open(os.path.join(adv_dir, "advisory_cdn_metadata.json"), "w") as f:
            f.write("{ invalid json }")

        # Create valid filelist (to get past the first file)
        with open(os.path.join(adv_dir, "advisory_cdn_filelist.json"), "w") as f:
            json.dump({}, f)

        with pytest.raises(ValueError) as exc_info:
            source = KonfluxSource(
                url=tmpdir, advisories="TEST-2020:0001", **PULP_PARAMS
            )
            with source:
                list(source)

        assert "Invalid JSON" in str(exc_info.value)


def test_context_manager():
    """Test context manager behavior."""
    source = KonfluxSource(url=DATADIR, advisories="RHSA-2020:0509", **PULP_PARAMS)

    # Executor should be running
    assert source._executor is not None

    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.anyio.run",
        side_effect=_mock_resolve_hrefs,
    ):
        with source:
            items = list(source)
            assert len(items) > 0

    # After exit, executor should be shutdown
    # (We can't easily test this without accessing private state)


def test_resolve_rpm_hrefs_success():
    """Test successful batch RPM resolution in Pulp."""
    source = KonfluxSource(url=DATADIR, advisories="RHSA-2020:0509", **PULP_PARAMS)

    # Mock Pulp3Client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    # build_query_sha256 is a sync method, use MagicMock
    mock_client.build_query_sha256 = MagicMock(
        return_value="(sha256=abc123 OR sha256=def456)"
    )
    mock_client.search_content.return_value = [
        {
            "pulp_href": "/pulp/api/v3/content/rpm/packages/abc-123/",
            "name": "test-rpm-1.0-1.x86_64.rpm",
            "sha256": "abc123",
        },
        {
            "pulp_href": "/pulp/api/v3/content/rpm/packages/def-456/",
            "name": "test-rpm-1.0-1.src.rpm",
            "sha256": "def456",
        },
    ]

    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.Pulp3Client",
        return_value=mock_client,
    ):
        result = anyio.run(source._resolve_rpm_hrefs, ["abc123", "def456"])

    assert result == {
        "abc123": "/pulp/api/v3/content/rpm/packages/abc-123/",
        "def456": "/pulp/api/v3/content/rpm/packages/def-456/",
    }
    mock_client.build_query_sha256.assert_called_once_with(["abc123", "def456"])
    mock_client.search_content.assert_called_once_with(
        query="(sha256=abc123 OR sha256=def456)",
        fields=["pulp_href", "name", "sha256"],
        limit=2,
    )


def test_resolve_rpm_hrefs_multiple_batches():
    """Test RPM resolution splits into multiple batches."""
    source = KonfluxSource(url=DATADIR, advisories="RHSA-2020:0509", **PULP_PARAMS)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.build_query_sha256 = MagicMock(
        side_effect=lambda sums: "(sha256=%s)" % sums[0]
    )
    mock_client.search_content.side_effect = [
        [
            {
                "pulp_href": "/pulp/api/v3/content/rpm/packages/abc-123/",
                "name": "test-rpm-1.0-1.x86_64.rpm",
                "sha256": "abc123",
            },
        ],
        [
            {
                "pulp_href": "/pulp/api/v3/content/rpm/packages/def-456/",
                "name": "test-rpm-1.0-1.src.rpm",
                "sha256": "def456",
            },
        ],
    ]

    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.Pulp3Client",
        return_value=mock_client,
    ):
        result = anyio.run(source._resolve_rpm_hrefs, ["abc123", "def456"], 1)

    assert result == {
        "abc123": "/pulp/api/v3/content/rpm/packages/abc-123/",
        "def456": "/pulp/api/v3/content/rpm/packages/def-456/",
    }
    assert mock_client.build_query_sha256.call_count == 2
    assert mock_client.search_content.call_count == 2


def test_resolve_rpm_hrefs_no_href():
    """Test RPM resolution when result has no pulp_href."""
    source = KonfluxSource(url=DATADIR, advisories="RHSA-2020:0509", **PULP_PARAMS)

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.build_query_sha256 = MagicMock(return_value="(sha256=abc123)")
    mock_client.search_content.return_value = [
        {
            "name": "test-rpm-1.0-1.x86_64.rpm",
            "sha256": "abc123",
        }
    ]

    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.Pulp3Client",
        return_value=mock_client,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            anyio.run(source._resolve_rpm_hrefs, ["abc123"])

    assert "has no pulp_href" in str(exc_info.value)


def test_rpm_not_found_in_pulp():
    """Test error when RPM SHA256 is not found in Pulp results."""
    source = KonfluxSource(url=DATADIR, advisories="RHBA-2020:1234", **PULP_PARAMS)

    # Mock _resolve_rpm_hrefs to return empty map (RPM not found)
    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.anyio.run"
    ) as mock_run:
        mock_run.return_value = {}  # No RPMs resolved

        with pytest.raises(RuntimeError) as exc_info:
            source._create_rpm_items(
                source._loader.load_advisory_data("RHBA-2020:1234")
            )

    assert "not found in Pulp" in str(exc_info.value)


def test_missing_sha256_checksum():
    """Test error when RPM has no SHA256 checksum in filelist."""
    source = KonfluxSource(url=DATADIR, advisories="RHBA-2020:1234", **PULP_PARAMS)

    # Load real data then remove sha256 checksums
    data = source._loader.load_advisory_data("RHBA-2020:1234")
    for build_data in data.filelist.values():
        build_data["checksums"]["sha256"] = {}

    with pytest.raises(RuntimeError) as exc_info:
        source._create_rpm_items(data)

    assert "No SHA256 checksum found" in str(exc_info.value)


def test_missing_pulp_url():
    """Test that missing pulp_url raises RuntimeError at construction."""
    with pytest.raises(RuntimeError) as exc_info:
        KonfluxSource(
            url=DATADIR,
            advisories="RHSA-2020:0509",
            pulp_cert="/path/to/cert",
            pulp_key="/path/to/key",
            pulp_domain="konflux-myteam-tenant",
        )

    assert "pulp_url" in str(exc_info.value)


def test_missing_pulp_domain():
    """Test that missing pulp_domain raises RuntimeError at construction."""
    with pytest.raises(RuntimeError) as exc_info:
        KonfluxSource(
            url=DATADIR,
            advisories="RHSA-2020:0509",
            pulp_url="https://pulp.example.com",
            pulp_cert="/path/to/cert",
            pulp_key="/path/to/key",
        )

    assert "pulp_domain" in str(exc_info.value)


def test_missing_pulp_auth():
    """Test that missing Pulp auth raises RuntimeError at construction."""
    with pytest.raises(RuntimeError) as exc_info:
        KonfluxSource(
            url=DATADIR,
            advisories="RHSA-2020:0509",
            pulp_url="https://pulp.example.com",
            pulp_domain="konflux-myteam-tenant",
        )

    assert "authentication not configured" in str(exc_info.value)


def test_basic_auth():
    """Test construction with username/password authentication."""
    source = KonfluxSource(
        url=DATADIR,
        advisories="RHSA-2020:0509",
        pulp_url="https://pulp.example.com",
        pulp_user="myuser",
        pulp_password="mypassword",
        pulp_domain="konflux-myteam-tenant",
    )

    assert source._pulp_client_kwargs["auth"] == ("myuser", "mypassword")
    assert "cert" not in source._pulp_client_kwargs


def test_build_without_rpms():
    """Test that builds without 'rpms' key are skipped."""
    source = KonfluxSource(url=DATADIR, advisories="RHBA-2020:1234", **PULP_PARAMS)

    data = source._loader.load_advisory_data("RHBA-2020:1234")

    # Add a build entry without 'rpms' key
    data.filelist["some-build-1.0-1.el8"] = {
        "checksums": {"md5": {}, "sha256": {}},
        "sig_key": "FD431D51",
    }

    with patch(
        "pushsource._impl.backend.konflux_source.konflux_source.anyio.run",
        side_effect=_mock_resolve_hrefs,
    ):
        items = source._create_rpm_items(data)

    # Should only have 1 RPM (from RHBA-2020:1234), not the build without rpms
    assert len(items) == 1
