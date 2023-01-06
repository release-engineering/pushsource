import os
import logging
from mock import patch

from pushsource import Source, RpmPushItem


DATADIR = os.path.join(os.path.dirname(__file__), "data")


def test_staged_simple_rpm(caplog):
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    files = list(source)

    files.sort(key=lambda item: item.src)

    # It should find the staged RPMs
    assert files == [
        RpmPushItem(
            name="walrus-5.21-1.noarch.rpm",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/RPMS/walrus-5.21-1.noarch.rpm"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            # Note this signing key was extracted from RPM headers.
            signing_key="F78FB195",
        ),
        RpmPushItem(
            name="test-srpm01-1.0-1.src.rpm",
            state="PENDING",
            src=os.path.join(staged_dir, "dest1/SRPMS/test-srpm01-1.0-1.src.rpm"),
            dest=["dest1"],
            md5sum=None,
            sha256sum=None,
            origin=staged_dir,
            build=None,
            signing_key=None,
        ),
    ]
    # It should also warn about this
    nonrpm_path = os.path.join(staged_dir, "dest1/RPMS/not-an-rpm.txt")
    msg = "Unexpected non-RPM %s (ignored)" % nonrpm_path
    assert msg in caplog.messages


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60"},
)
@patch("pushsource._impl.backend.staged.staged_source.time.sleep")
@patch(
    "pushsource._impl.backend.staged.staged_source.StagedSource._push_items_for_leafdir"
)
@patch("pushsource._impl.backend.staged.staged_source.StagedSource._load_metadata")
@patch("pushsource._impl.backend.staged.staged_source.os.path.exists")
def test_staged_simple_rpm_wait_nonexistent_path(
    mock_path_exists,
    mock_load_metadata,
    mock_push_items_for_leafdir,
    mock_sleep,
    caplog,
):
    caplog.set_level(logging.INFO)
    mock_path_exists.return_value = False
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    list(source)

    mock_sleep.assert_called_once()
    mock_load_metadata.assert_called_once()
    mock_push_items_for_leafdir.assert_called()

    assert "doesn't exist yet. Waiting for 60 seconds." in caplog.records[1].message


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60", "PUSHSOURCE_APPLY_WAIT_TOPDIR_AGE": "100"},
)
@patch("pushsource._impl.backend.staged.staged_source.time.time")
@patch("pushsource._impl.backend.staged.staged_source.time.sleep")
@patch(
    "pushsource._impl.backend.staged.staged_source.StagedSource._push_items_for_leafdir"
)
@patch("pushsource._impl.backend.staged.staged_source.StagedSource._load_metadata")
@patch("pushsource._impl.backend.staged.staged_source.os.path.exists")
@patch("pushsource._impl.backend.staged.staged_source.os.path.getmtime")
def test_staged_simple_rpm_recent_dir_mtime_wait(
    mock_getmtime,
    mock_path_exists,
    mock_load_metadata,
    mock_push_items_for_leafdir,
    mock_sleep,
    mock_time,
    caplog,
):
    caplog.set_level(logging.INFO)
    mock_time.return_value = 1000
    mock_getmtime.return_value = 950
    mock_path_exists.return_value = True
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    list(source)

    mock_sleep.assert_called_once()
    mock_load_metadata.assert_called_once()
    mock_push_items_for_leafdir.assert_called()

    assert (
        "has mtime 1970-01-01T00:15:50+00:00, being less than 100 seconds old. "
        "Waiting for 60 seconds." in caplog.records[1].message
    )


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60", "PUSHSOURCE_APPLY_WAIT_TOPDIR_AGE": "100"},
)
@patch("pushsource._impl.backend.staged.staged_source.time.time")
@patch("pushsource._impl.backend.staged.staged_source.time.sleep")
@patch(
    "pushsource._impl.backend.staged.staged_source.StagedSource._push_items_for_leafdir"
)
@patch("pushsource._impl.backend.staged.staged_source.StagedSource._load_metadata")
@patch("pushsource._impl.backend.staged.staged_source.os.path.exists")
@patch("pushsource._impl.backend.staged.staged_source.os.path.getmtime")
def test_staged_simple_rpm_older_dir_skip_wait(
    mock_getmtime,
    mock_path_exists,
    mock_load_metadata,
    mock_push_items_for_leafdir,
    mock_sleep,
    mock_time,
    caplog,
):
    caplog.set_level(logging.INFO)
    mock_time.return_value = 1000
    mock_getmtime.return_value = 700
    mock_path_exists.return_value = True
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    list(source)

    mock_sleep.assert_not_called()
    mock_load_metadata.assert_called_once()
    mock_push_items_for_leafdir.assert_called()

    assert (
        "has mtime 1970-01-01T00:11:40+00:00, being more than 100 seconds old. "
        "Skipping the wait." in caplog.records[1].message
    )


@patch.dict(
    "os.environ",
    {"PUSHSOURCE_SRC_POLL_TIMEOUT": "60", "PUSHSOURCE_APPLY_WAIT_TOPDIR_AGE": "0"},
)
@patch("pushsource._impl.backend.staged.staged_source.time.time")
@patch("pushsource._impl.backend.staged.staged_source.time.sleep")
@patch(
    "pushsource._impl.backend.staged.staged_source.StagedSource._push_items_for_leafdir"
)
@patch("pushsource._impl.backend.staged.staged_source.StagedSource._load_metadata")
@patch("pushsource._impl.backend.staged.staged_source.os.path.exists")
@patch("pushsource._impl.backend.staged.staged_source.os.path.getmtime")
def test_staged_simple_rpm_age_check_disabled(
    mock_getmtime,
    mock_path_exists,
    mock_load_metadata,
    mock_push_items_for_leafdir,
    mock_sleep,
    mock_time,
    caplog,
):
    caplog.set_level(logging.INFO)
    mock_time.return_value = 1000
    mock_getmtime.return_value = 1000
    mock_path_exists.return_value = True
    staged_dir = os.path.join(DATADIR, "simple_rpm")
    source = Source.get("staged:" + staged_dir)

    list(source)

    mock_sleep.assert_not_called()
    mock_load_metadata.assert_called_once()
    mock_push_items_for_leafdir.assert_called()

    assert (
        "has mtime 1970-01-01T00:16:40+00:00, being more than 0 seconds old. "
        "Skipping the wait." in caplog.records[1].message
    )
