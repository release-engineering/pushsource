import logging
from concurrent import futures

from more_executors import Executors

from ...helpers import (
    as_completed_with_timeout_reset,
    force_https,
    list_argument,
    try_int,
)
from ...model import AmiPushItem
from ...source import Source
from .pub_client import PubClient

LOG = logging.getLogger("pushsource")


class PubSource(Source):
    """Uses push item list from Pub as the source of push items."""

    def __init__(
        self,
        url,
        task_id,
        threads=4,
        timeout=60 * 60 * 4,
    ):
        """Create a new source.

        Parameters:
            url (src)
                Base URL of Pub Tool, e.g. "http://pub.example.com",
                "https://pub.example.com:8123".

            task_id (int, str, list[str], list[int])
                Task ID(s) to be used as push item source.
                If a single string is given, multiple IDs may be
                comma-separated.

            threads (int)
                Number of threads used for concurrent queries to Pub.

            timeout (int)
                Number of seconds after which an error is raised, if no progress is
                made during queries to Pub.
        """

        self._url = force_https(url)
        self._task_ids = self._validate_task_ids(
            [try_int(x) for x in list_argument(task_id)]
        )
        self._client = PubClient(threads=threads, url=self._url)
        self._timeout = timeout
        # This executor doesn't use retry because pub-client executor already does that.
        self._executor = Executors.thread_pool(
            name="pushsource-pub", max_workers=threads
        ).with_cancel_on_shutdown()

    def _validate_task_ids(self, task_ids):
        out = []
        for task_id in task_ids:
            if isinstance(task_id, int):
                out.append(task_id)
            else:
                LOG.warning("Invalid Pub task ID: %s", task_id)
        return out

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.shutdown()
        self._executor.shutdown(True)

    def _push_items_from_ami_json(self, json_obj):
        out = []

        try:
            push_items = AmiPushItem._from_data(json_obj)
            out.extend(list_argument(push_items))
        except KeyError:
            LOG.warning("Cannot parse AMI push item/s: %s", str(json_obj))

        return out

    def __iter__(self):
        # Get json Pub responses for all task ids
        json_fs = [self._client.get_ami_json_f(task_id) for task_id in self._task_ids]

        # Convert them to lists of push items
        push_items_fs = []
        for f in futures.as_completed(json_fs, timeout=self._timeout):
            push_items_fs.append(
                self._executor.submit(self._push_items_from_ami_json, f.result())
            )

        completed_fs = as_completed_with_timeout_reset(
            push_items_fs, timeout=self._timeout
        )
        for f in completed_fs:
            for pushitem in f.result():
                yield pushitem


Source.register_backend("pub", PubSource)
