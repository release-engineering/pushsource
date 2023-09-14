import mock
import logging
import subprocess

import pytest

from pushsource._impl.backend.errata_source.errata_client import ErrataHTTPClient

@pytest.fixture(autouse=True)
def fake_temporary_file(mocker):
    mock_file = mocker.patch("tempfile.NamedTemporaryFile")
    mock_file.return_value.__enter__.return_value.name = (
        "/temp/ccache_pushsource_errata_1234"
    )


@mock.patch("subprocess.run")
def test_authenticate_already_exists(mock_run):
    client = ErrataHTTPClient(1,
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    mock_run.return_value.stdout = "Default principal: pub-errata@IPA.REDHAT.COM\n"
    mock_run.return_value.returncode = 0

    client.authenticate()
    mock_run.assert_called_once_with(
        ["klist", "-c", "FILE:/temp/ccache_pushsource_errata_1234"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


@mock.patch("subprocess.run")
def test_authenticate_not_found(mock_run, caplog):
    caplog.set_level(logging.INFO)

    client = ErrataHTTPClient(1,
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    ret1 = mock.MagicMock()
    ret1.stdout = "No TGT exists"
    ret1.returncode = 0
    ret2 = mock.MagicMock()
    ret2.stdout = "success"
    ret2.returncode = 0
    mock_run.side_effect = [ret1, ret2]

    client.authenticate()
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0] == mock.call(
        ["klist", "-c", "FILE:/temp/ccache_pushsource_errata_1234"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert mock_run.call_args_list[1] == mock.call(
        [
            "kinit",
            "pub-errata@IPA.REDHAT.COM",
            "-k",
            "-t",
            "/path/to/keytab",
            "-c",
            "FILE:/temp/ccache_pushsource_errata_1234",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert caplog.messages == [
        "Errata TGT doesn't exist, running kinit "
        "for principal pub-errata@IPA.REDHAT.COM"
    ]


@mock.patch("subprocess.run")
def test_authenticate_kinit_failed(mock_run, caplog):
    caplog.set_level(logging.INFO)

    client = ErrataHTTPClient(1,
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    ret1 = mock.MagicMock()
    ret1.stdout = "No TGT exists"
    ret1.returncode = 0
    ret2 = mock.MagicMock()
    ret2.stdout = "kinit failed"
    ret2.returncode = 1
    mock_run.side_effect = [ret1, ret2]

    client.authenticate()
    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0] == mock.call(
        ["klist", "-c", "FILE:/temp/ccache_pushsource_errata_1234"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert mock_run.call_args_list[1] == mock.call(
        [
            "kinit",
            "pub-errata@IPA.REDHAT.COM",
            "-k",
            "-t",
            "/path/to/keytab",
            "-c",
            "FILE:/temp/ccache_pushsource_errata_1234",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert caplog.messages == [
        "Errata TGT doesn't exist, running kinit "
        "for principal pub-errata@IPA.REDHAT.COM",
        "kinit has failed: 'kinit failed'",
    ]


