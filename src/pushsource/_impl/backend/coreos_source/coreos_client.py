import json
import logging
import os
import re
import threading
from urllib.parse import urlparse, urlunparse


import requests
from more_executors import Executors

LOG = logging.getLogger("pushsource.coreos_client")


class CoreOSClient(object):
    def __init__(self, url, threads=4, timeout=60 * 60, **retry_args):
        self._executor = (
            Executors.thread_pool(name="pushsource-coreos-client", max_workers=threads)
            .with_map(self._unpack_response)
            .with_retry(**retry_args)
            .with_timeout(timeout)
            .with_cancel_on_shutdown()
        )
        self._url = url
        self._tls = threading.local()

    def shutdown(self):
        self._executor.shutdown(True)

    def _unpack_response(self, response):
        try:
            response.raise_for_status()
            out = response.json()
        except json.JSONDecodeError:
            # do not treat invalid json as fatal error
            out = None
        return out

    @property
    def _session(self):
        if not hasattr(self._tls, "session"):
            LOG.debug(
                "Creating requests Session for client of CoreOS service: %s", self._url
            )
            self._tls.session = requests.Session()
        return self._tls.session

    def _do_request(self, method, url):
        return self._session.request(method, url)

    @staticmethod
    def convert_github_blob_to_raw(url, path):
        """Convert github.com/.../blob/... to raw.githubusercontent.com URL."""
        _GITHUB_BLOB_RE = re.compile(
            r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(blob|tree)/(?P<ref>[^/]+)(?:/(?P<path>.+))?$"
        )

        # Strip query params and fragment from the URL
        full_url = os.path.join(url, path)
        parsed_url = urlparse(full_url)
        clean_url = urlunparse(parsed_url._replace(query="", fragment=""))

        m = _GITHUB_BLOB_RE.match(clean_url.rstrip("/"))
        if not m:
            return clean_url  # already raw or non-GitHub
        d = m.groupdict()

        # Use the shorter raw form which handles branches, tags, and commit SHAs
        # without needing to distinguish between refs/heads or refs/tags
        raw_url = f"https://raw.githubusercontent.com/{d['owner']}/{d['repo']}/{d['ref']}/{d['path']}"
        LOG.info("Converted URL %s to %s", parsed_url, raw_url)
        return raw_url

    def get_json_f(self, path):
        """Returns Future[dict|list] holding json obj with VMI push items returned from CoreOS installer file.

        Parameters:
            path (str)
                Path to the JSON file containing the CoreOS installer information.
                Eg.: "data/data/coreos/rhcos.json"
        """
        url = self.convert_github_blob_to_raw(self._url, path)
        LOG.info("Fetching VMI push items from CoreOS installer file: %s", url)
        ft = self._executor.submit(self._do_request, method="GET", url=url)
        return ft
