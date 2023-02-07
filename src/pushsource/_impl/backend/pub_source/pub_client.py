import json
import logging
import os
import threading


import requests
from more_executors import Executors


LOG = logging.getLogger("pushsource.pub_client")


class PubClient(object):
    def __init__(self, threads, url, **retry_args):
        self._executor = (
            Executors.thread_pool(name="pushsource-pub-client", max_workers=threads)
            .with_map(self._unpack_response)
            .with_retry(**retry_args)
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
                "Creating requests Session for client of Pub service: %s", self._url
            )
            self._tls.session = requests.Session()
        return self._tls.session

    def _do_request(self, **kwargs):
        return self._session.request(**kwargs)

    def get_ami_json_f(self, task_id):
        """
        Returns Future[dict|list] holding json obj with AMI push items returned from Pub for given task id.
        """
        endpoint = "pub/task"
        url_ending = "log/images.json"
        params = {"format": "raw"}
        url = os.path.join(self._url, endpoint, str(task_id), url_ending)

        LOG.info("Requesting Pub service for %s of task: %s", url_ending, str(task_id))
        ft = self._executor.submit(
            self._do_request, method="GET", url=url, params=params
        )

        return ft
