from functools import partial
import logging
import os
import re
import subprocess
import tempfile
import threading
import xmlrpc.client as xmlrpc_client  # nosec B411
from urllib.parse import urljoin
import warnings

import gssapi
from more_executors import Executors
from more_executors.futures import f_zip, f_map
import requests
import requests_gssapi

from ...compat_attr import attr

LOG = logging.getLogger("pushsource.errata_client")

USE_XMLRPC_CLIENT = os.environ.get("PUSHSOURCE_ERRATA_USE_XMLRPC_API") == "1"


def get_errata_client(
    threads,
    url,
    keytab_path=None,
    principal=None,
    force_xmlrpc=USE_XMLRPC_CLIENT,
    **retry_kwargs,
):
    keytab_path = (
        os.environ.get("PUSHSOURCE_ERRATA_KEYTAB_PATH")
        if not keytab_path
        else keytab_path
    )
    principal = (
        os.environ.get("PUSHSOURCE_ERRATA_PRINCIPAL") if not principal else principal
    )
    if keytab_path and principal and not force_xmlrpc:
        return ErrataHTTPClient(threads, url, keytab_path, principal, **retry_kwargs)
    return ErrataClient(threads, url, **retry_kwargs)


@attr.s()
class ErrataRaw(object):
    # Helper to collect raw responses of all ET APIs for a single advisory
    advisory_cdn_metadata = attr.ib(type=dict)
    advisory_cdn_file_list = attr.ib(type=dict)
    advisory_cdn_docker_file_list = attr.ib(type=dict)
    ftp_paths = attr.ib(type=dict)


# pylint: disable=W0223
class ErrataClientBase(object):
    def __init__(self, threads, url, **retry_args):
        self._executor = (
            Executors.thread_pool(name="pushsource-errata-client", max_workers=threads)
            .with_retry(**retry_args)
            .with_cancel_on_shutdown()
        )
        self._url = url
        self._tls = threading.local()

    def authenticate(self):
        pass

    def get_advisory_data(self, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    def _get_advisory_cdn_metadata(self, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    def _get_advisory_cdn_file_list(self, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    def _get_advisory_cdn_docker_file_list(self, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    def _get_ftp_paths(self, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    @property
    def _errata_service(self):
        raise NotImplementedError()  # pragma: no cover

    def _do_call(self, method, advisory_id):
        raise NotImplementedError()  # pragma: no cover

    def shutdown(self):
        self._executor.shutdown(True)

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

    def _call_et(self, method, advisory_id):
        # These APIs have had performance issues occasionally, so let's set up some
        # detailed structured logs which can be used to check the performance.
        LOG.debug(
            "Calling Errata Tool %s(%s)",
            method,
            advisory_id,
            extra={
                "event": {
                    "type": "errata-tool-call-start",
                    "method": method,
                    "advisory": advisory_id,
                }
            },
        )
        try:
            out = self._do_call(method, advisory_id)

            LOG.debug(
                "Errata Tool completed call %s(%s)",
                method,
                advisory_id,
                extra={
                    "event": {
                        "type": "errata-tool-call-end",
                        "method": method,
                        "advisory": advisory_id,
                    }
                },
            )

            return out
        except:
            LOG.debug(
                "Failed to call Errata Tool %s(%s)",
                method,
                advisory_id,
                extra={
                    "event": {
                        "type": "errata-tool-call-fail",
                        "method": method,
                        "advisory": advisory_id,
                    }
                },
            )
            raise


class ErrataClient(ErrataClientBase):
    def __init__(self, threads, url, **retry_args):
        deprecation_notice = (
            "The XMLRPC Errata Client has been deprecated and will be removed. "
            "Please provide a `keytab_path` and `principal` to the errata "
            "pushsource backend."
        )
        warnings.warn(deprecation_notice, category=DeprecationWarning)

        super().__init__(threads, url, **retry_args)

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

    def get_advisory_data(self, advisory_id):
        # This isn't available via the xml-rpc  api, only via http
        return None

    @property
    def _errata_service(self):
        # XML-RPC client connected to errata_service.
        # Each thread uses a separate client.
        if not hasattr(self._tls, "errata_service"):
            LOG.debug("Creating XML-RPC client for Errata Tool: %s", self._url)
            self._tls.errata_service = xmlrpc_client.ServerProxy(self._url)
        return self._tls.errata_service

    def _do_call(self, method, advisory_id):
        service_method = getattr(self._errata_service, method)
        return service_method(advisory_id)


class ErrataHTTPClient(ErrataClientBase):
    def __init__(self, threads, url, keytab_path: str, principal: str, **retry_args):
        super().__init__(threads, url, **retry_args)

        self.keytab_path = keytab_path
        self.principal = principal

        self.get_advisory_data = partial(self._call_et, "/api/v1/erratum/{id}")
        self._get_advisory_cdn_metadata = partial(
            self._call_et, "/api/v1/push_metadata/cdn_metadata/{id}.json"
        )
        self._get_advisory_cdn_file_list = partial(
            self._call_et, "/api/v1/push_metadata/cdn_file_list/{id}.json"
        )
        self._get_advisory_cdn_docker_file_list = partial(
            self._call_et, "/api/v1/push_metadata/cdn_docker_file_list/{id}.json"
        )
        self._get_ftp_paths = partial(
            self._call_et, "/api/v1/push_metadata/ftp_paths/{id}.json"
        )

        with tempfile.NamedTemporaryFile(
            prefix="ccache_pushsource_errata_", delete=False
        ) as file:
            self.ccache_filename = file.name

    def authenticate(self):
        """
        Use the keytab to create a Kerberos ticket granting ticket.

        This method is expected to be called before any HTTP queries to errata are made.
        """

        result = subprocess.run(
            ["klist", "-c", f"FILE:{self.ccache_filename}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        regex_res = re.search(r"Default principal: (.*)\n", result.stdout)

        # if Kerberos ticket is not found, or the principal is incorrect
        if result.returncode or not regex_res or regex_res.group(1) != self.principal:
            LOG.info(
                "Errata TGT doesn't exist, running kinit for principal %s",
                self.principal,
            )
            result = subprocess.run(
                [
                    "kinit",
                    self.principal,
                    "-k",
                    "-t",
                    self.keytab_path,
                    "-c",
                    f"FILE:{self.ccache_filename}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if result.returncode:
                LOG.warning("kinit has failed: '%s'", result.stdout)

    @property
    def _errata_service(self):
        """
        Create requests Session.

        Session is used so that Kerberos authentication only has to be done once.
        As pushsource utilizes threading, and sessions are not thread safe, each thread
        will have a separate session.

        Returns (object):
            Authenticated requests Session object.
        """

        if not hasattr(self._tls, "session"):
            LOG.debug("Creating HTTP client for Errata Tool: %s", self._url)
            name = gssapi.Name(self.principal, gssapi.NameType.user)
            creds = gssapi.Credentials.acquire(
                name=name,
                usage="initiate",
                store={"ccache": f"FILE:{self.ccache_filename}"},
            ).creds

            session = requests.Session()
            session.auth = requests_gssapi.HTTPSPNEGOAuth(creds=creds)
            self._tls.session = session

        return self._tls.session

    def _do_call(self, method, advisory_id):
        complete_api_path = method.format(id=advisory_id)
        url = urljoin(self._url, complete_api_path)
        response = self._errata_service.get(url)

        response.raise_for_status()

        return response.json()
