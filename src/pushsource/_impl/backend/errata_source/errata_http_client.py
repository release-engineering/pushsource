import os
import threading
import subprocess
import re
import logging
import tempfile
from urllib.parse import urljoin

import requests
import gssapi
import requests_gssapi

LOG = logging.getLogger("pushsource.errata_http_client")


class ErrataHTTPClient:
    """Class for performing HTTP API queries with Errata."""

    def __init__(self, hostname: str, keytab_path: str = None, principal: str = None):
        """
        Initialize.

        Args:
            hostname (str):
                Errata hostname.
            keytab_path (str):
                Path to a keytab used to perform Kerberos authentication with Errata.
                If not set, env variable PUSHSOURCE_ERRATA_KEYTAB_PATH will be used.
            principal (str):
                Kerberos principal.
                If not set, env variable PUSHSOURCE_ERRATA_PRINCIPAL will be used.
        """
        self.hostname = hostname
        # Generate a random filename for ccache
        with tempfile.NamedTemporaryFile(
            prefix="ccache_pushsource_errata_", delete=False
        ) as file:
            self.ccache_filename = file.name

        if keytab_path:
            self.keytab_path = keytab_path
        else:
            self.keytab_path = os.environ.get("PUSHSOURCE_ERRATA_KEYTAB_PATH", None)

        if principal:
            self.principal = principal
        else:
            self.principal = os.environ.get("PUSHSOURCE_ERRATA_PRINCIPAL", None)

        # requests Sessions will be local per thread
        self._thread_local = threading.local()

    def create_kerberos_ticket(self):
        """
        Use the keytab to create a Kerberos ticket granting ticket.

        This method is expected to be called before any HTTP queries to errata are made.
        """
        if not self.keytab_path or not self.principal:
            LOG.warning(
                "Errata principal or keytab path is not specified. Skipping creating TGT"
            )
            return

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
    def session(self) -> requests.Session:
        """
        Create requests Session.

        Session is used so that Kerberos authentication only has to be done once.
        As pushsource utilizes threading, and sessions are not thread safe, each thread
        will have a separate session.

        Returns (object):
            Authenticated requests Session object.
        """

        if not hasattr(self._thread_local, "session"):
            LOG.debug("Creating Errata requests session")
            name = gssapi.Name(self.principal, gssapi.NameType.user)
            creds = gssapi.Credentials.acquire(
                name=name,
                usage="initiate",
                store={"ccache": f"FILE:{self.ccache_filename}"},
            ).creds

            session = requests.Session()
            session.auth = requests_gssapi.HTTPSPNEGOAuth(creds=creds)
            self._thread_local.session = session

        return self._thread_local.session

    def get_advisory_data(self, advisory: str) -> dict:
        """
        Get advisory data.

        Uses endpoint GET /api/v1/erratum/{id}.

        Args:
            advisory (str):
                Advisory ID or name.
        Returns (dict):
            Parsed JSON data as returned by Errata.
        """
        url = urljoin(self.hostname, f"/api/v1/erratum/{advisory}")
        LOG.info("Queried Errata HTTP API for %s", advisory)
        response = self.session.get(url)
        response.raise_for_status()

        return response.json()
