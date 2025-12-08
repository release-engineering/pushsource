import os

import pytest
from mock import patch

from pushsource import Source, RpmPushItem


@pytest.fixture
def source_factory(fake_errata_tool, fake_koji, koji_dir):
    # Yields constructor for an errata source pointing at a valid advisory with RPMs,
    # with no arch filter set. Tests can then provide a specific filter and observe
    # the results.
    source_ctor = Source.get_partial(
        "errata:https://errata.example.com",
        errata="RHSA-2020:0509",
        koji_source="koji:https://koji.example.com?basedir=%s" % koji_dir,
    )

    # Insert koji RPMs referenced by this advisory
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-1.8.25p1-4.el8_0.3.src.rpm"] = {
        "arch": "src",
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debuginfo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "sudo-debuginfo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm"] = {
        "arch": "ppc64le",
        "name": "sudo-debugsource",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }
    fake_koji.rpm_data["sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "sudo-debugsource",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "build_id": 1234,
    }

    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "sudo",
        "version": "1.8.25p1",
        "release": "4.el8_0.3",
        "nvr": "sudo-1.8.25p1-4.el8_0.3",
    }
    fake_koji.build_data["sudo-1.8.25p1-4.el8_0.3"] = fake_koji.build_data[1234]

    signed_rpm_path = os.path.join(
        koji_dir,
        "vol/somevol/packages/foobuild/1.0/1.el8",
        "data/signed/def456/x86_64/foo-1.0-1.x86_64.rpm",
    )

    # Make signed RPMs exist (contents not relevant here)
    for filename, rpm in fake_koji.rpm_data.items():
        signed_rpm_path = os.path.join(
            koji_dir,
            "packages/sudo/1.8.25p1/4.el8_0.3/",
            "data/signed/fd431d51/%s/%s" % (rpm["arch"], filename),
        )
        signed_dir = os.path.dirname(signed_rpm_path)
        if not os.path.exists(signed_dir):
            os.makedirs(signed_dir)
        open(signed_rpm_path, "w")

    yield source_ctor


@pytest.mark.parametrize(
    "rpm_filter_arch,expected_filenames",
    [
        (
            "ppc64le",
            [
                "sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                "sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                "sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
            ],
        ),
        (
            # Checks amd64 => x86_64 conversion
            "ppc64le,amd64",
            [
                "sudo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                "sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                "sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                "sudo-debuginfo-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                "sudo-debugsource-1.8.25p1-4.el8_0.3.ppc64le.rpm",
                "sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm",
            ],
        ),
        (
            # Proper lists also work
            ["x86_64", "SRPM"],
            [
                "sudo-1.8.25p1-4.el8_0.3.src.rpm",
                "sudo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                "sudo-debuginfo-1.8.25p1-4.el8_0.3.x86_64.rpm",
                "sudo-debugsource-1.8.25p1-4.el8_0.3.x86_64.rpm",
            ],
        ),
        (
            # Empty filter also works and gives nothing
            [],
            [],
        ),
    ],
)
@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header", return_value="fd431d51")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_errata_rpms_filtered_by_arch(
    mock_get_rpm_header, mock_get_keys_from_headers, source_factory, rpm_filter_arch, expected_filenames
):
    """Errata source can filter produced RPMs by arch"""

    source = source_factory(rpm_filter_arch=rpm_filter_arch)

    items = list(source)
    rpm_items = [i for i in items if isinstance(i, RpmPushItem)]
    filenames = sorted([i.name for i in rpm_items])
    assert filenames == sorted(expected_filenames)
