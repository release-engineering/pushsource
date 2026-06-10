import json
from unittest import mock

from pushsource._impl.backend.coreos_source.coreos_client import CoreOSClient


class TestCoreOSClient:
    def test_convert_github_blob_to_raw(self):
        expected_raw_url = "https://raw.githubusercontent.com/openshift/installer/master/data/data/coreos/rhcos.json"
        actual_raw_url = CoreOSClient.convert_github_blob_to_raw(
            "https://github.com/openshift/installer/tree/master",
            "data/data/coreos/rhcos.json",
        )
        assert actual_raw_url == expected_raw_url

        non_github_url = "https://example.com/some/path/file.json"
        actual_raw_url = CoreOSClient.convert_github_blob_to_raw(
            "https://example.com/some/path", "file.json"
        )
        assert actual_raw_url == "https://example.com/some/path/file.json"

    def test_shutdown(self, mock_coreos_client):
        with mock.patch.object(
            mock_coreos_client._executor, "shutdown"
        ) as mock_shutdown:
            mock_coreos_client.shutdown()
            mock_shutdown.assert_called_once_with(True)

    def test_get_json_f(self, mock_coreos_client):
        with mock.patch.object(mock_coreos_client, "_do_request") as mock_do_request:
            # Test successful JSON decoding
            mock_response_success = mock.Mock()
            mock_response_success.json.return_value = {"key": "value"}
            mock_response_success.raise_for_status.return_value = None
            mock_do_request.return_value = mock_response_success

            test_url = "https://raw.githubusercontent.com/openshift/installer/master/data/data/coreos/test.json"
            mock_coreos_client.convert_github_blob_to_raw = (
                lambda base_url, path: test_url
            )

            future = mock_coreos_client.get_json_f("data/data/coreos/test.json")
            result = future.result()
            assert result == {"key": "value"}
            mock_do_request.assert_called_once_with(method="GET", url=test_url)

            # Test JSONDecodeError handling
            mock_do_request.reset_mock()
            mock_response_json_error = mock.Mock()
            mock_response_json_error.json.side_effect = json.JSONDecodeError(
                "msg", "doc", 0
            )
            mock_response_json_error.raise_for_status.return_value = None
            mock_do_request.return_value = mock_response_json_error

            future_error = mock_coreos_client.get_json_f("data/data/coreos/test.json")
            result_error = future_error.result()
            assert result_error is None
            mock_do_request.assert_called_once_with(method="GET", url=test_url)

    def test_session_property_initialization(self, mock_coreos_client):
        # Ensure session is created only once per thread
        # First access, session should be created
        session1 = mock_coreos_client._session
        with mock.patch("requests.Session") as mock_session_class:
            # Second access, session should not be created again
            session2 = mock_coreos_client._session
            mock_session_class.assert_not_called()  # Should not be called again
            assert session1 is session2

    def test_do_request(self, mock_coreos_client):
        # Ensure _tls.session is initialized
        _ = mock_coreos_client._session
        with mock.patch.object(mock_coreos_client._tls, "session") as mock_session:
            mock_response = mock.Mock()
            mock_session.request.return_value = mock_response

            method = "GET"
            url = "http://example.com/api"
            result = mock_coreos_client._do_request(method, url)

            mock_session.request.assert_called_once_with(method, url)
            assert result == mock_response
