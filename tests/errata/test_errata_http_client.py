import mock
import logging
import subprocess

import requests_mock
import pytest
import requests

from pushsource._impl.backend.errata_source.errata_http_client import ErrataHTTPClient


@pytest.fixture(autouse=True)
def fake_temporary_file(mocker):
    mock_file = mocker.patch("tempfile.NamedTemporaryFile")
    mock_file.return_value.__enter__.return_value.name = (
        "/temp/ccache_pushsource_errata_1234"
    )


def test_init():
    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    assert client.hostname == "https://errata.example.com/"
    assert client.keytab_path == "/path/to/keytab"
    assert client.principal == "pub-errata@IPA.REDHAT.COM"
    assert client.ccache_filename == "/temp/ccache_pushsource_errata_1234"


@mock.patch.dict(
    "os.environ",
    {
        "PUSHSOURCE_ERRATA_KEYTAB_PATH": "/path/to/keytab",
        "PUSHSOURCE_ERRATA_PRINCIPAL": "pub-errata@IPA.REDHAT.COM",
    },
)
def test_init_env_vars():
    client = ErrataHTTPClient("https://errata.example.com/")

    assert client.hostname == "https://errata.example.com/"
    assert client.keytab_path == "/path/to/keytab"
    assert client.principal == "pub-errata@IPA.REDHAT.COM"


@mock.patch("subprocess.run")
def test_create_kerberos_ticket_already_exists(mock_run):
    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    mock_run.return_value.stdout = "Default principal: pub-errata@IPA.REDHAT.COM\n"
    mock_run.return_value.returncode = 0

    client.create_kerberos_ticket()
    mock_run.assert_called_once_with(
        ["klist", "-c", "FILE:/temp/ccache_pushsource_errata_1234"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


@mock.patch("subprocess.run")
def test_create_kerberos_ticket_not_found(mock_run, caplog):
    caplog.set_level(logging.INFO)

    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    ret1 = mock.MagicMock()
    ret1.stdout = "No TGT exists"
    ret1.returncode = 0
    ret2 = mock.MagicMock()
    ret2.stdout = "success"
    ret2.returncode = 0
    mock_run.side_effect = [ret1, ret2]

    client.create_kerberos_ticket()
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
def test_create_kerberos_ticket_kinit_failed(mock_run, caplog):
    caplog.set_level(logging.INFO)

    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )

    ret1 = mock.MagicMock()
    ret1.stdout = "No TGT exists"
    ret1.returncode = 0
    ret2 = mock.MagicMock()
    ret2.stdout = "kinit failed"
    ret2.returncode = 1
    mock_run.side_effect = [ret1, ret2]

    client.create_kerberos_ticket()
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


@mock.patch("subprocess.run")
def test_create_kerberos_ticket_skip(mock_run, caplog):
    caplog.set_level(logging.INFO)

    client = ErrataHTTPClient("https://errata.example.com/")

    client.create_kerberos_ticket()
    assert mock_run.call_count == 0
    assert caplog.messages == [
        "Errata principal or keytab path is not specified. Skipping creating TGT"
    ]


@mock.patch("gssapi.Name")
@mock.patch("gssapi.Credentials.acquire")
@mock.patch("requests.Session")
@mock.patch("requests_gssapi.HTTPSPNEGOAuth")
def test_get_session(mock_auth, mock_session, mock_acquire, mock_name, caplog):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    assert not hasattr(client._thread_local, "session")

    session = client.session

    mock_name.assert_called_once()
    mock_acquire.assert_called_once_with(
        name=mock_name.return_value,
        usage="initiate",
        store={"ccache": "FILE:/temp/ccache_pushsource_errata_1234"},
    )
    mock_session.assert_called_once_with()
    mock_auth.assert_called_once_with(creds=mock_acquire.return_value.creds)

    assert session == mock_session.return_value
    assert client._thread_local.session == mock_session.return_value

    assert caplog.messages == ["Creating Errata requests session"]


@mock.patch("gssapi.Name")
@mock.patch("gssapi.Credentials.acquire")
@mock.patch("requests.Session")
@mock.patch("requests_gssapi.HTTPSPNEGOAuth")
def test_get_session_already_exists(
    mock_auth, mock_session, mock_acquire, mock_name, caplog
):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    assert not hasattr(client._thread_local, "session")
    session_mock = client._thread_local.session = mock.MagicMock()
    session = client.session

    mock_name.assert_not_called()
    mock_acquire.assert_not_called()
    mock_session.assert_not_called()
    mock_auth.assert_not_called()

    assert session == session_mock
    assert caplog.messages == []


def test_get_advisory_data(caplog):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    client._thread_local.session = requests.Session()
    with requests_mock.Mocker() as m:
        m.get(
            "https://errata.example.com/api/v1/erratum/RHSA-123456789",
            json={"errata": "data"},
        )

        data = client.get_advisory_data("RHSA-123456789")

    assert data == {"errata": "data"}
    assert m.call_count == 1
    assert caplog.messages == [
        "Queried Errata HTTP API for RHSA-123456789",
        "GET https://errata.example.com/api/v1/erratum/RHSA-123456789 200",
    ]
