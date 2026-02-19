import os
import json
import tempfile
import pytest

from pushsource._impl.backend.konflux_source.konflux_loader import (
    KonfluxLoader,
    KonfluxAdvisoryData,
)


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_load_advisory_data():
    """Test loading advisory data successfully."""
    loader = KonfluxLoader(DATADIR)
    data = loader.load_advisory_data("RHSA-2020:0509")

    assert isinstance(data, KonfluxAdvisoryData)
    assert data.advisory_id == "RHSA-2020:0509"
    assert isinstance(data.metadata, dict)
    assert isinstance(data.filelist, dict)

    # Check metadata has expected keys
    assert "id" in data.metadata
    assert "title" in data.metadata
    assert "severity" in data.metadata

    # Check filelist has expected structure
    assert "sudo-1.8.25p1-4.el8_0.3" in data.filelist
    assert "rpms" in data.filelist["sudo-1.8.25p1-4.el8_0.3"]
    assert "checksums" in data.filelist["sudo-1.8.25p1-4.el8_0.3"]


def test_missing_advisory_directory():
    """Test error when advisory directory doesn't exist."""
    loader = KonfluxLoader(DATADIR)

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_advisory_data("NONEXISTENT-2020:9999")

    assert "Required file not found" in str(exc_info.value)
    assert "advisory_cdn_metadata.json" in str(exc_info.value)


def test_missing_metadata_file():
    """Test error when metadata file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create advisory directory with only filelist
        adv_dir = os.path.join(tmpdir, "TEST-2020:0001")
        os.makedirs(adv_dir)

        with open(os.path.join(adv_dir, "advisory_cdn_filelist.json"), "w") as f:
            json.dump({}, f)

        loader = KonfluxLoader(tmpdir)

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_advisory_data("TEST-2020:0001")

        assert "advisory_cdn_metadata.json" in str(exc_info.value)


def test_missing_filelist_file():
    """Test error when filelist file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create advisory directory with only metadata
        adv_dir = os.path.join(tmpdir, "TEST-2020:0001")
        os.makedirs(adv_dir)

        with open(os.path.join(adv_dir, "advisory_cdn_metadata.json"), "w") as f:
            json.dump({"id": "TEST-2020:0001"}, f)

        loader = KonfluxLoader(tmpdir)

        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_advisory_data("TEST-2020:0001")

        assert "advisory_cdn_filelist.json" in str(exc_info.value)


def test_invalid_json_metadata():
    """Test error when metadata JSON is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_dir = os.path.join(tmpdir, "TEST-2020:0001")
        os.makedirs(adv_dir)

        # Create invalid JSON
        with open(os.path.join(adv_dir, "advisory_cdn_metadata.json"), "w") as f:
            f.write("{ this is not valid json }")

        with open(os.path.join(adv_dir, "advisory_cdn_filelist.json"), "w") as f:
            json.dump({}, f)

        loader = KonfluxLoader(tmpdir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_advisory_data("TEST-2020:0001")

        assert "Invalid JSON" in str(exc_info.value)
        assert "advisory_cdn_metadata.json" in str(exc_info.value)


def test_invalid_json_filelist():
    """Test error when filelist JSON is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_dir = os.path.join(tmpdir, "TEST-2020:0001")
        os.makedirs(adv_dir)

        with open(os.path.join(adv_dir, "advisory_cdn_metadata.json"), "w") as f:
            json.dump({"id": "TEST-2020:0001"}, f)

        # Create invalid JSON
        with open(os.path.join(adv_dir, "advisory_cdn_filelist.json"), "w") as f:
            f.write("{ not valid json }")

        loader = KonfluxLoader(tmpdir)

        with pytest.raises(ValueError) as exc_info:
            loader.load_advisory_data("TEST-2020:0001")

        assert "Invalid JSON" in str(exc_info.value)
        assert "advisory_cdn_filelist.json" in str(exc_info.value)


def test_metadata_content():
    """Test that metadata content is correctly loaded and structured."""
    loader = KonfluxLoader(DATADIR)
    data = loader.load_advisory_data("RHSA-2020:0509")

    # Verify specific metadata fields
    assert data.metadata["id"] == "RHSA-2020:0509"
    assert data.metadata["severity"] == "Important"
    assert data.metadata["type"] == "security"
    assert "sudo" in data.metadata["title"]

    # Verify additional metadata structure
    assert "pkglist" in data.metadata
    assert "references" in data.metadata
    assert "description" in data.metadata


def test_filelist_content():
    """Test that filelist content is correctly loaded and structured."""
    loader = KonfluxLoader(DATADIR)
    data = loader.load_advisory_data("RHSA-2020:0509")

    # Verify build exists in filelist
    build_data = data.filelist["sudo-1.8.25p1-4.el8_0.3"]

    # Verify top-level structure
    assert "rpms" in build_data
    assert "checksums" in build_data
    assert "sig_key" in build_data
    assert build_data["sig_key"] == "fd431d51"

    # Verify a specific RPM and its repositories
    assert "sudo-1.8.25p1-4.el8_0.3.x86_64.rpm" in build_data["rpms"]
    rpm_repos = build_data["rpms"]["sudo-1.8.25p1-4.el8_0.3.x86_64.rpm"]
    assert "rhel-8-for-x86_64-baseos-e4s-rpms__8_DOT_0" in rpm_repos

    # Verify checksums structure
    checksums = build_data["checksums"]

    # Should have md5 and sha256
    assert "md5" in checksums
    assert "sha256" in checksums

    # Each should be a dict of filename -> checksum
    assert isinstance(checksums["md5"], dict)
    assert isinstance(checksums["sha256"], dict)

    # Verify specific checksums for the x86_64 RPM
    assert (
        checksums["md5"]["sudo-1.8.25p1-4.el8_0.3.x86_64.rpm"]
        == "25e9470c4fe96034fe1d7525c04b5d8e"
    )
    assert (
        checksums["sha256"]["sudo-1.8.25p1-4.el8_0.3.x86_64.rpm"]
        == "593f872c1869f7beb963c8df2945fc691a1d999945c8c45c6bc7e02731fa016f"
    )
