import logging
import os

import pytest
import requests

from pushsource._impl.backend.pub_source import pub_client


@pytest.fixture
def test_client():
    client = pub_client.PubClient(1, "https://test.example.com/")
    yield client
    client.shutdown()


def test_pub_client_successful_request(requests_mock, caplog, test_client):
    """
    Test Pub client behavior for succesule response from service.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri("GET", request_url, json={"test": "OK"})

    # do request to service
    client = test_client
    json_ft = client.get_ami_json_f(100)

    # we should get proper json response
    assert json_ft.result() == {"test": "OK"}
    # following lines are captured in logs
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 200",
    ]


def test_pub_client_corrupted_json(requests_mock, caplog, test_client):
    """
    Test Pub client behavior when no json or corrupted json is returned from service.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri("GET", request_url, text="vcccccc")

    # do request to service
    client = test_client
    json_ft = client.get_ami_json_f(100)

    # we get None as response because of no valid json content
    assert json_ft.result() == None
    # following lines are captured in logs
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 200",
    ]


def test_pub_client_404_status(requests_mock, caplog, test_client):
    """
    Test Pub client behavior for 404 status code returned from service.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri("GET", request_url, text="Not Found", status_code=404)
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/clouds.json?format=raw"
    )
    requests_mock.register_uri("GET", request_url, text="Not Found", status_code=404)

    # do request to service - 404 raises exception
    with pytest.raises(requests.exceptions.HTTPError) as exc:
        client = test_client
        json_ft = client.get_ami_json_f(100)
        json_ft.result()

    # following lines are captured in logs - more line due to retries
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 404",
        "GET https://test.example.com/pub/task/100/log/clouds.json?format=raw 404",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 404",
        "GET https://test.example.com/pub/task/100/log/clouds.json?format=raw 404",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 404",
        "GET https://test.example.com/pub/task/100/log/clouds.json?format=raw 404",
    ]
    # check exception value
    assert (
        "404 Client Error: None for url: https://test.example.com/pub/task/100/log/clouds.json?format=raw"
        in str(exc.value)
    )


def test_pub_client_500_status(requests_mock, caplog, test_client):
    """
    Test Pub client behavior for 500 status code returned from service.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri(
        "GET", request_url, text="Internal server error", status_code=500
    )

    # do request to service - 505 raises exception
    with pytest.raises(requests.exceptions.HTTPError) as exc:
        client = test_client
        json_ft = client.get_ami_json_f(100)
        json_ft.result()

    # following lines are captured in logs - more line due to retries
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
    ]

    # check exception value
    assert (
        "500 Server Error: None for url: https://test.example.com/pub/task/100/log/images.json?format=raw"
        in str(exc.value)
    )


def test_pub_client_500_status(requests_mock, caplog, test_client):
    """
    Test Pub client behavior for 500 status code returned from service.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri(
        "GET", request_url, text="Internal server error", status_code=500
    )

    # do request to service - 505 raises exception
    with pytest.raises(requests.exceptions.HTTPError) as exc:
        client = test_client
        json_ft = client.get_ami_json_f(100)
        json_ft.result()

    # following lines are captured in logs - more line due to retries
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
        "GET https://test.example.com/pub/task/100/log/images.json?format=raw 500",
    ]

    # check exception value
    assert (
        "500 Server Error: None for url: https://test.example.com/pub/task/100/log/images.json?format=raw"
        in str(exc.value)
    )


def test_pub_client_timeout_error(requests_mock, caplog, test_client):
    """
    Test Pub client behavior for timeout exception while sending request.
    """
    # test setup
    caplog.set_level(logging.DEBUG)
    task_id = 100
    url = "https://test.example.com"
    request_url = os.path.join(
        url, "pub/task", str(task_id), "log/images.json?format=raw"
    )
    requests_mock.register_uri("GET", request_url, exc=requests.exceptions.Timeout)

    # do request to service - Timeout exception
    with pytest.raises(requests.exceptions.Timeout):
        client = test_client
        json_ft = client.get_ami_json_f(100)
        json_ft.result()

    # following lines are captured in log.
    assert caplog.messages == [
        "Fetching AMI details from Pub task: 100",
        "Creating requests Session for client of Pub service: https://test.example.com/",
    ]
