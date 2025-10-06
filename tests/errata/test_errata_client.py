import mock
import logging
import subprocess

import requests_mock
import pytest
import requests

from pushsource._impl.backend.errata_source.errata_client import (
    ERRATA_RETRY_STRATEGY,
    ErrataHTTPClient,
    get_errata_client,
)


@pytest.fixture(autouse=True)
def fake_temporary_file(mocker):
    mock_file = mocker.patch("tempfile.NamedTemporaryFile")
    mock_file.return_value.__enter__.return_value.name = (
        "/temp/ccache_pushsource_errata_1234"
    )


@mock.patch.dict(
    "os.environ",
    {
        "PUSHSOURCE_ERRATA_KEYTAB_PATH": "/path/to/keytab",
        "PUSHSOURCE_ERRATA_PRINCIPAL": "pub-errata@IPA.REDHAT.COM",
    },
)
def test_init_env_vars():
    client = get_errata_client(1, "https://errata.example.com/")

    assert client._url == "https://errata.example.com/"
    assert client.keytab_path == "/path/to/keytab"
    assert client.principal == "pub-errata@IPA.REDHAT.COM"


@mock.patch("requests.adapters.HTTPAdapter")
@mock.patch("gssapi.Name")
@mock.patch("gssapi.Credentials.acquire")
@mock.patch("requests.Session")
@mock.patch("requests_gssapi.HTTPSPNEGOAuth")
def test_get_session(
    mock_auth, mock_session, mock_acquire, mock_name, mock_adapter, caplog
):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        1, "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    assert not hasattr(client._tls, "session")

    session = client._errata_service

    mock_name.assert_called_once()
    mock_acquire.assert_called_once_with(
        name=mock_name.return_value,
        usage="initiate",
        store={"ccache": "FILE:/temp/ccache_pushsource_errata_1234"},
    )
    mock_session.assert_called_once_with()
    mock_auth.assert_called_once_with(creds=mock_acquire.return_value.creds)
    mock_adapter.assert_called_once_with(max_retries=ERRATA_RETRY_STRATEGY)
    assert session.mount.call_count == 2

    assert session == mock_session.return_value
    assert client._tls.session == mock_session.return_value

    assert caplog.messages == [
        "Creating HTTP client for Errata Tool: " "https://errata.example.com/"
    ]


@mock.patch("gssapi.Name")
@mock.patch("gssapi.Credentials.acquire")
@mock.patch("requests.Session")
@mock.patch("requests_gssapi.HTTPSPNEGOAuth")
def test_get_session_already_exists(
    mock_auth, mock_session, mock_acquire, mock_name, caplog
):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        1, "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    assert not hasattr(client._tls, "session")
    session_mock = client._tls.session = mock.MagicMock()
    session = client._errata_service

    mock_name.assert_not_called()
    mock_acquire.assert_not_called()
    mock_session.assert_not_called()
    mock_auth.assert_not_called()

    assert session == session_mock
    assert caplog.messages == []


def test_get_advisory_data(caplog):
    caplog.set_level(logging.DEBUG)

    client = ErrataHTTPClient(
        1, "https://errata.example.com/", "/path/to/keytab", "pub-errata@IPA.REDHAT.COM"
    )
    client._tls.session = requests.Session()
    with requests_mock.Mocker() as m:
        m.get(
            "https://errata.example.com/api/v1/erratum/RHSA-123456789",
            json={"errata": "data"},
        )

        data = client.get_advisory_data("RHSA-123456789")

    assert data == {"errata": "data"}
    assert m.call_count == 1
    assert caplog.messages == [
        "Calling Errata Tool /api/v1/erratum/{id}(RHSA-123456789)",
        "GET https://errata.example.com/api/v1/erratum/RHSA-123456789 200",
        "Errata Tool completed call /api/v1/erratum/{id}(RHSA-123456789)",
    ]
