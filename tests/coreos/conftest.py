import os
import json
from unittest import mock

import pytest

from pushsource._impl.backend.coreos_source.coreos_client import CoreOSClient


@pytest.fixture
def mock_coreos_client():
    with mock.patch(
        "pushsource._impl.backend.coreos_source.coreos_client.requests.Session"
    ):
        yield CoreOSClient(url="https://github.com/openshift/installer/tree/master")


@pytest.fixture
def coreos_rhel_9_data():
    filepath = os.path.join(os.path.dirname(__file__), "data", "coreos-rhel-9.json")
    with open(filepath, "r") as f:
        return json.load(f)


@pytest.fixture
def coreos_rhel_10_data():
    filepath = os.path.join(os.path.dirname(__file__), "data", "coreos-rhel-10.json")
    with open(filepath, "r") as f:
        return json.load(f)


@pytest.fixture
def coreos_missing_data():
    filepath = os.path.join(
        os.path.dirname(__file__), "data", "coreos-missing-data.json"
    )
    with open(filepath, "r") as f:
        return json.load(f)
