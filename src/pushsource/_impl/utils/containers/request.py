import base64
import hashlib
import json

import os
import six

try:
    from json.decoder import JSONDecodeError

    JSONException = JSONDecodeError
except ImportError:  # pragma: no cover
    JSONException = ValueError

from six.moves.urllib import parse as urlparse
from requests.adapters import HTTPAdapter

# pylint: disable-next=import-error
from requests.packages.urllib3.util import Retry
from requests import Session, exceptions

try:
    import urllib2 as request
except ImportError:
    # Yes, there's a six.moves for this import, but,
    # parse_http_list and parse_keqv_list are no available
    # in python-six package from RHEL6, these alias
    # were included in a recent six version.
    from urllib import request


MEDIATYPE_SCHEMA2_V1 = "application/vnd.docker.distribution.manifest.v1+json"
MEDIATYPE_SCHEMA2_V1_SIGNED = (
    "application/vnd.docker.distribution.manifest.v1+prettyjws"
)
MEDIATYPE_SCHEMA2_V2 = "application/vnd.docker.distribution.manifest.v2+json"
MEDIATYPE_SCHEMA2_V2_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"


class AuthToken(object):
    def __init__(self, token=None):
        self.token = token


def update_auth_header(headers, token):
    """
    Adds the token into the request's headers as specified in the Docker v2 API documentation.
    https://docs.docker.com/registry/spec/auth/token/#using-the-bearer-token
    """
    headers.update({"authorization": "Bearer %s" % token})
    return headers


def request_token(session, response, credentials, repo_name):
    """
    Attempts to retrieve the correct token based on the 401 response header.
    According to the Docker API v2 documentation, the token be retrieved by issuing a GET
    request to the url specified by the `realm` within the `WWW-Authenticate` header. This
    request should add the following query parameters:
        service: the name of the service that hosts the desired resource
        scope:   the specific resource and permissions requested
    https://docs.docker.com/registry/spec/auth/token/#requesting-a-token
    """
    auth_info = parse_401_response_headers(response.headers)
    try:
        token_url = auth_info.pop("realm")
    except KeyError as e:
        six.raise_from(IOError("No realm specified for token auth challenge."), e)

    if "scope" not in auth_info and repo_name:
        auth_info["scope"] = "repository:%s:pull" % repo_name

    parse_result = urlparse.urlparse(token_url)
    query_dict = urlparse.parse_qs(parse_result.query)
    query_dict.update(auth_info)
    url_pieces = list(parse_result)
    url_pieces[4] = urlparse.urlencode(query_dict)
    token_url = urlparse.urlunparse(url_pieces)

    http_opts = {}
    if credentials:
        # whenever token is requested, we need to send original
        # credentials again. On the other hand we don't want them stored
        # int http_opts, as it would override Bearer token
        http_opts["auth"] = credentials

    session.mount(
        token_url, HTTPAdapter(max_retries=Retry(total=3, status_forcelist=[500, 404]))
    )
    session.headers.pop("authorization", None)
    response = session.get(token_url, **http_opts)
    response.raise_for_status()

    return response.json()["token"]


def parse_401_response_headers(response_headers):
    """
    Parse the headers from a 401 response into a dictionary that contains the information
    necessary to retrieve a token.
    Example:
    Www-Authenticate: Bearer realm="https://auth.docker.io/token",
    service="registry.docker.io",scope="repository:library/nginx:pull,push"
    """
    auth_header = response_headers.get("www-authenticate")
    if auth_header is None:
        raise IOError(
            "401 responses are expected to contain authentication information"
        )
    auth_header = auth_header[len("Bearer ") :]

    # The remaining string consists of comma separated key=value pairs
    # according to RFC 2617
    try:
        items = request.parse_http_list(auth_header)
        return request.parse_keqv_list(items)
    except ValueError as e:
        six.raise_from(
            IOError("401 responses are expected to contain authentication information"),
            e,
        )


def registry_request(
    session,
    uri,
    action="get",
    auth_token=None,
    retry_404=True,
    headers=None,
    data=None,
    credentials=None,
    http_opts=None,
    repo=None,
):
    """
    Retrieve a single path within the upstream registry, and return a
    2-tuple of the headers and the response body.
    """
    status_forcelist = [500]
    if retry_404:
        status_forcelist.append(404)
    if headers is None:
        headers = {}
    if http_opts is None:
        http_opts = {}
    assert isinstance(headers, dict)
    http_opts = http_opts or {}

    session.mount(
        uri,
        HTTPAdapter(
            max_retries=Retry(
                total=3,
                backoff_factor=1.0,  # 1.0, 2.0, 4.0, 8.0, ...
                status_forcelist=status_forcelist,
            )
        ),
    )
    if auth_token.token:
        update_auth_header(headers, auth_token.token)

    _request = getattr(session, action)
    try:
        response = _request(uri, headers=headers, data=data, **http_opts)
        response.raise_for_status()
    except exceptions.HTTPError as e:
        if e.response.status_code == 401:
            auth_header = e.response.headers.get("www-authenticate") or ""
            auth_header = auth_header.lower()
            if auth_header.startswith("bearer"):
                auth_token.token = request_token(session, response, credentials, repo)
                update_auth_header(headers, auth_token.token)
            elif auth_header.startswith("basic"):
                http_opts["auth"] = credentials
            else:
                raise
            response = _request(uri, headers=headers, data=data, **http_opts)
            response.raise_for_status()
        else:
            raise
    return response


def get_basic_auth(host, home=None):
    # Look for docker config file in home directory for username and password
    home_dir = os.path.expanduser("~")
    conf_file = os.path.join(home or home_dir, ".docker/config.json")
    if os.path.isfile(conf_file):
        with open(conf_file) as f:
            config = json.load(f)
            auth = config.get("auths", {}).get(host, {}).get("auth")
            if auth:
                return tuple(base64.b64decode(auth).decode().split(":"))
    return None, None


# Copied from https://github.com/pulp/pulp_docker.git
def _calculate_digest(raw_manifest, manifest):
    _raw_manifest = raw_manifest
    if "signatures" in manifest:
        protected = manifest["signatures"][0]["protected"]
        paddings = {0: "", 2: "==", 3: "="}
        protected += paddings[len(protected) % 4]
        unprotected = json.loads(base64.b64decode(protected))
        signed_length = unprotected["formatLength"]
        signed_tail = base64.b64decode(
            unprotected["formatTail"] + paddings[len(unprotected["formatTail"]) % 4]
        )
        _raw_manifest = raw_manifest[:signed_length] + signed_tail
    digest = "{a}:{d}".format(a="sha256", d=hashlib.sha256(_raw_manifest).hexdigest())
    return digest


def get_manifest(registry, repo, digest, manifest_types=None, token=None):
    auth = get_basic_auth(registry.split("://")[1])
    token = token or AuthToken()

    if manifest_types is None:
        manifest_types = [MEDIATYPE_SCHEMA2_V1, MEDIATYPE_SCHEMA2_V1_SIGNED]
    headers = {"Accept": ",".join(manifest_types)}
    session = Session()
    try:
        resp = registry_request(
            session,
            "%s/v2/%s/manifests/%s" % (registry, repo, digest),
            action="get",
            auth_token=token,
            retry_404=True,
            credentials=auth,
            headers=headers,
            repo=repo,
        )
        digest = resp.headers.get("docker-content-digest", None)
        if not digest:
            digest = _calculate_digest(resp.content, resp.json())

        content_type = resp.headers.get("Content-Type", None)
    except exceptions.HTTPError as e:
        try:
            json_error = e.response.json()
        except (ValueError, JSONException):
            json_error = {}
        if e.response.status_code == 404 and (
            "MANIFEST_UNKNOWN" in [err["code"] for err in json_error.get("errors", [])]
            or "TAG_EXPIRED" in [err["code"] for err in json_error.get("errors", [])]
        ):
            six.raise_from(
                KeyError(
                    "Failed to get the manifest for image '%s' [%s]" % (repo, digest)
                ),
                e,
            )
            # otherwise probably true 404 or other error, let's reraise it
        raise e
    return content_type, digest, resp.json()


def get_blob(registry, repo, digest, token=None):
    auth = get_basic_auth(registry.split("://")[1])
    token = token or AuthToken()
    session = Session()
    resp = registry_request(
        session,
        "%s/v2/%s/blobs/%s" % (registry, repo, digest),
        action="get",
        auth_token=token,
        retry_404=True,
        credentials=auth,
        repo=repo,
    )
    resp.raise_for_status()
    return resp


def api_version_check(registry, token=None, credentials=None):
    """
    Make a call to the registry URL's /v2/ API call to determine if the registry supports API
    v2.
    """
    token = token or AuthToken()
    session = Session()
    if not credentials:
        auth = get_basic_auth(registry.split("://")[1])
    else:
        auth = credentials
    try:
        response = registry_request(
            session, "%s/v2/" % registry, credentials=auth, auth_token=token
        )
    except exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False
        raise e
    try:
        version = response.headers["Docker-Distribution-API-Version"]
        if version != "registry/2.0":
            return False
    except KeyError:
        # If the Docker-Distribution-API-Version header isn't present, we will assume that this
        # is a valid Docker 2.0 API server so that simple file-based webservers can serve as our
        # remote feed.
        pass
    return True


def inspect(registry, repo, digest, token=None):
    token = token or AuthToken()

    manifest_type, digest, manifest = get_manifest(
        registry, repo, digest, manifest_types=[MEDIATYPE_SCHEMA2_V2], token=token
    )
    if manifest_type == MEDIATYPE_SCHEMA2_V2:
        inspected = get_blob(registry, repo, manifest["config"]["digest"]).json()
    elif manifest_type == MEDIATYPE_SCHEMA2_V2_LIST:
        manifest_type, _digest, manifest = get_manifest(
            registry,
            repo,
            manifest["manifests"][0]["digest"],
            manifest_types=[MEDIATYPE_SCHEMA2_V2],
            token=token,
        )
        inspected = get_blob(registry, repo, manifest["config"]["digest"]).json()
    else:
        inspected = {"architecture": manifest["architecture"], "config": {"Labels": {}}}
    if manifest_type == MEDIATYPE_SCHEMA2_V2 and not inspected.get("config", {}).get(
        "Labels"
    ):
        inspected["source"] = True
    inspected["digest"] = digest
    return inspected
