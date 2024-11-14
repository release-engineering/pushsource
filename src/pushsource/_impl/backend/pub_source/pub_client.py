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

    def _do_request(self, url, **kwargs):
        kwargs["url"] = url.format(filename="images.json")
        resp = self._session.request(**kwargs)
        # if 404 lets try clouds.json
        if resp.status_code == 404:
            kwargs["url"] = url.format(filename="clouds.json")
            resp = self._session.request(**kwargs)
        return resp

    def get_json_f(self, task_id):
        """
        Returns Future[dict|list] holding json obj with AMI or VHD
        push items returned from Pub for given task id.
        """
        endpoint = "pub/task"
        url_ending = "log/{filename}"
        params = {"format": "raw"}
        url = os.path.join(self._url, endpoint, str(task_id), url_ending)

        LOG.info("Fetching AMI/VHD details from Pub task: %s", str(task_id))
        ft = self._executor.submit(
            self._do_request, method="GET", url=url, params=params
        )

        return ft
