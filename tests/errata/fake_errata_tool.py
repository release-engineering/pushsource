import os
import yaml

from six.moves.xmlrpc_client import Fault


DATADIR = os.path.join(os.path.dirname(__file__), "data")


class FakeErrataToolController(object):
    def __init__(self):
        self.last_url = None
        self._data = self._load()

    def proxy(self, url):
        self.last_url = url
        return FakeErrataToolProxy(self)

    @classmethod
    def _load(cls):
        out = {}
        for root, _, files in os.walk(DATADIR):
            for filename in files:
                if filename.endswith(".yaml"):
                    path = os.path.join(root, filename)
                    with open(path) as fh:
                        data = yaml.load(fh, Loader=yaml.FullLoader)
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

    def _get_data(self, advisory_id, key):
        out = self._ctrl._data[advisory_id]
        if out is None:
            raise Fault(100, "No such advisory: %s" % advisory_id)
        return out.get(key, {})

    def get_advisory_cdn_file_list(self, advisory_id):
        return self._get_data(advisory_id, "cdn_file_list")

    def get_advisory_cdn_metadata(self, advisory_id):
        return self._get_data(advisory_id, "cdn_metadata")

    def get_advisory_cdn_docker_file_list(self, advisory_id):
        return self._get_data(advisory_id, "cdn_docker_file_list")

    def get_ftp_paths(self, advisory_id):
        return self._get_data(advisory_id, "ftp_paths")
