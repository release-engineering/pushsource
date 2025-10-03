import os
import re
from mock import Mock
import yaml
import json
from xmlrpc.client import Fault  # nosec B411
from urllib3.util.retry import Retry

import requests

DATADIR = os.path.join(os.path.dirname(__file__), "data")


class FakeErrataToolController(object):
    def __init__(self):
        self._data = self._load()
        self._errata_data = self._load_errata()
        self.last_url = None

    def proxy(self, url=""):
        if url:
            self.last_url = url
        return FakeErrataToolProxy(self)

    @classmethod
    def _load_errata(cls):
        out = {}
        for root, _, files in os.walk(DATADIR):
            for filename in files:
                if filename.endswith(".json"):
                    path = os.path.join(root, filename)
                    with open(path) as fh:
                        out[filename.rstrip(".json")] = json.load(fh)
        return out

    @classmethod
    def _load(cls):
        out = {}
        for root, _, files in os.walk(DATADIR):
            for filename in files:
                if filename.endswith(".yaml"):
                    path = os.path.join(root, filename)
                    with open(path) as fh:
                        data = yaml.load(fh, Loader=yaml.FullLoader)  # nosec B506
                    advisory_id = data["advisory_id"]
                    if advisory_id in out:
                        raise ValueError(
                            "Duplicate test data for advisory %s" % advisory_id
                        )
                    out[advisory_id] = data
        return out


class FakeErrataToolProxy(object):
    def __init__(self, controller):
        self._ctrl = controller
        self.auth = None
        self.mount = Mock(spec=Retry)
        self.url_map = [
            (".*/api/v1/erratum/(.*)", self.get_advisory_data),
            (
                ".*/api/v1/push_metadata/cdn_metadata/(.*).json",
                self.get_advisory_cdn_metadata,
            ),
            (
                ".*/api/v1/push_metadata/cdn_file_list/(.*).json",
                self.get_advisory_cdn_file_list,
            ),
            (
                ".*/api/v1/push_metadata/cdn_docker_file_list/(.*).json",
                self.get_advisory_cdn_docker_file_list,
            ),
            (".*/api/v1/push_metadata/ftp_paths/(.*).json", self.get_ftp_paths),
        ]

    def _get_data(self, advisory_id, key):
        out = self._ctrl._data[advisory_id]
        if out is None:
            raise Fault(100, "No such advisory: %s" % advisory_id)
        return out.get(key, {})

    def get_advisory_data(self, advisory_id):
        return self._ctrl._errata_data[advisory_id]

    def get_advisory_cdn_file_list(self, advisory_id):
        return self._get_data(advisory_id, "cdn_file_list")

    def get_advisory_cdn_metadata(self, advisory_id):
        return self._get_data(advisory_id, "cdn_metadata")

    def get_advisory_cdn_docker_file_list(self, advisory_id):
        return self._get_data(advisory_id, "cdn_docker_file_list")

    def get_ftp_paths(self, advisory_id):
        return self._get_data(advisory_id, "ftp_paths")

    def get(self, url, *args, **kwargs):
        response_object = Mock(spec=requests.models.Response)
        for path_regex, func in self.url_map:
            match = re.match(path_regex, url)
            if match:
                try:
                    response_object.json.return_value = func(match.group(1))
                    response_object.status_code = 200
                except Fault:
                    response_object.json.return_value = {
                        "error": "Bad errata id given: %s".format(match.group(1))
                    }
                    response_object.status_code = 404
                    response_object.raise_for_status.side_effect = requests.HTTPError()
                return response_object
        response_object.json.return_value = {}
        response_object.status_code = 404
        response_object.raise_for_status.side_effect = requests.HTTPError()
        return response_object
