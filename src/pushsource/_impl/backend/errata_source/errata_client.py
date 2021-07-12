import logging
import threading
from functools import partial

from six.moves import xmlrpc_client
from more_executors import Executors
from more_executors.futures import f_zip, f_map

from ...compat_attr import attr

LOG = logging.getLogger("pushsource.errata_client")


@attr.s()
class ErrataRaw(object):
    # Helper to collect raw responses of all ET APIs for a single advisory
    advisory_cdn_metadata = attr.ib(type=dict)
    advisory_cdn_file_list = attr.ib(type=dict)
    advisory_cdn_docker_file_list = attr.ib(type=dict)
    ftp_paths = attr.ib(type=dict)


class ErrataClient(object):
    def __init__(self, threads, url, **retry_args):
        self._executor = (
            Executors.thread_pool(name="pushsource-errata-client", max_workers=threads)
            .with_retry(**retry_args)
            .with_cancel_on_shutdown()
        )
        self._url = url
        self._tls = threading.local()

        self._get_advisory_cdn_metadata = partial(
            self._call_et, "get_advisory_cdn_metadata"
        )
        self._get_advisory_cdn_file_list = partial(
            self._call_et, "get_advisory_cdn_file_list"
        )
        self._get_advisory_cdn_docker_file_list = partial(
            self._call_et, "get_advisory_cdn_docker_file_list"
        )
        self._get_ftp_paths = partial(self._call_et, "get_ftp_paths")

    def shutdown(self):
        self._executor.shutdown(True)

    @property
    def _errata_service(self):
        # XML-RPC client connected to errata_service.
        # Each thread uses a separate client.
        if not hasattr(self._tls, "errata_service"):
            LOG.debug("Creating XML-RPC client for Errata Tool: %s", self._url)
            self._tls.errata_service = xmlrpc_client.ServerProxy(self._url)
        return self._tls.errata_service

    def _log_queried_et(self, response, advisory_id):
        # This message is visible by default for all advisories.
        # For more detailed logs of each individual call, see DEBUG logs
        # in _call_et.
        LOG.info("Queried Errata Tool for %s", advisory_id)
        return response

    def get_raw_f(self, advisory_id):
        """Returns Future[ErrataRaw] holding all ET responses for a particular advisory."""
        all_responses = f_zip(
            self._executor.submit(self._get_advisory_cdn_metadata, advisory_id),
            self._executor.submit(self._get_advisory_cdn_file_list, advisory_id),
            self._executor.submit(self._get_advisory_cdn_docker_file_list, advisory_id),
            self._executor.submit(self._get_ftp_paths, advisory_id),
        )
        all_responses = f_map(
            all_responses, partial(self._log_queried_et, advisory_id=advisory_id)
        )
        return f_map(all_responses, lambda tup: ErrataRaw(*tup))

    def _call_et(self, method_name, advisory_id):
        method = getattr(self._errata_service, method_name)

        # These APIs have had performance issues occasionally, so let's set up some
        # detailed structured logs which can be used to check the performance.
        LOG.debug(
            "Calling Errata Tool %s(%s)",
            method_name,
            advisory_id,
            extra={
                "event": {
                    "type": "errata-tool-call-start",
                    "method": method_name,
                    "advisory": advisory_id,
                }
            },
        )
        try:
            out = method(advisory_id)
            LOG.debug(
                "Errata Tool completed call %s(%s)",
                method_name,
                advisory_id,
                extra={
                    "event": {
                        "type": "errata-tool-call-end",
                        "method": method_name,
                        "advisory": advisory_id,
                    }
                },
            )
            return out
        except:
            LOG.debug(
                "Failed to call Errata Tool %s(%s)",
                method_name,
                advisory_id,
                extra={
                    "event": {
                        "type": "errata-tool-call-fail",
                        "method": method_name,
                        "advisory": advisory_id,
                    }
                },
            )
            raise
