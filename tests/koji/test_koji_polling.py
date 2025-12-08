from typing import Any


import os
from mock import patch

from pushsource import Source, RpmPushItem

DATADIR = os.path.join(os.path.dirname(__file__), "data")

@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60"},
)
@patch("pushsource._impl.helpers.os.path.exists")
@patch("pushsource._impl.helpers.time.sleep")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_koji_poll_for_signed_rpm_highest_priority_key_present(
    mock_get_rpm_header, mock_get_keys_from_headers, mock_sleep, mock_path_exists, fake_koji, koji_dir, caplog
):
    """Highest priority key becomes present after some time."""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm",
        basedir=koji_dir,
        signing_key=["ABC123", None, "DEF456"],
    )

    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    signed_rpm_path = os.path.join(
        koji_dir,
        "vol/somevol/packages/foobuild/1.0/1.el8",
        "data/signed/abc123/x86_64/foo-1.0-1.x86_64.rpm",
    )
    mock_path_exists.side_effect = [False, True, True, True]
    mock_get_keys_from_headers.return_value = "abc123"

    # Eagerly fetch
    items = list(source)

    # It should have found the RPM using the signing key we created within testdata
    assert items[0] == RpmPushItem(
        name="foo-1.0-1.x86_64.rpm",
        state="PENDING",
        src=signed_rpm_path,
        build="foobuild-1.0-1.el8",
        signing_key="abc123",
    )
    assert len(items) == 1
    assert mock_sleep.call_count == 1


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60"},
)
@patch("pushsource._impl.helpers.os.path.exists")
@patch("pushsource._impl.helpers.time.sleep")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_keys_from_header")
@patch("pushsource._impl.backend.koji_source.rpmlib.get_rpm_header")
def test_koji_poll_for_signed_rpm_highest_priority_key_absent(
    mock_get_rpm_header, mock_get_keys_from_headers, mock_sleep, mock_path_exists, fake_koji, koji_dir, caplog
):
    """Highest priority key is always absent and a lower priority key is found."""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm",
        basedir=koji_dir,
        signing_key=["ABC123", None, "DEF456"],
    )

    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    signed_rpm_path = os.path.join(
        koji_dir,
        "vol/somevol/packages/foobuild/1.0/1.el8",
        "data/signed/def456/x86_64/foo-1.0-1.x86_64.rpm",
    )
    mock_path_exists.side_effect = [False, False, False, False, False, True, True, True]
    mock_get_keys_from_headers.return_value = "def456"
    # Eagerly fetch
    items = list(source)

    # It should have found the RPM using the signing key we return from RPM headers
    assert items[0] == RpmPushItem(
        name="foo-1.0-1.x86_64.rpm",
        state="PENDING",
        src=signed_rpm_path,
        build="foobuild-1.0-1.el8",
        signing_key="def456",
    )
    assert len(items) == 1
    assert mock_sleep.call_count == 2


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60"},
)
@patch("pushsource._impl.helpers.time.sleep")
def test_koji_missing_signing_key_timeout(mock_sleep, fake_koji, koji_dir, caplog):
    """RPM is NOTFOUND if requested signing key is not available."""

    source = Source.get(
        "koji:https://koji.example.com/?rpm=foo-1.0-1.x86_64.rpm&signing_key=abc123",
        basedir=koji_dir,
    )

    fake_koji.rpm_data["foo-1.0-1.x86_64.rpm"] = {
        "arch": "x86_64",
        "name": "foo",
        "version": "1.0",
        "release": "1",
        "build_id": 1234,
    }
    fake_koji.build_data[1234] = {
        "id": 1234,
        "name": "foobuild",
        "version": "1.0",
        "release": "1.el8",
        "nvr": "foobuild-1.0-1.el8",
        "volume_name": "somevol",
    }

    # Eagerly fetch
    items = list(source)

    # It should be counted as NOTFOUND...
    assert items == [RpmPushItem(name="foo-1.0-1.x86_64.rpm", state="NOTFOUND")]

    # ...for this reason
    expected_path = (
        "%s/vol/somevol/packages/foobuild/1.0/1.el8/data/signed/abc123/x86_64/foo-1.0-1.x86_64.rpm"
        % koji_dir
    )
    expected_msg = "RPM not found in koji at path(s): %s" % expected_path
    assert expected_msg in caplog.messages
    assert mock_sleep.call_count == 2
