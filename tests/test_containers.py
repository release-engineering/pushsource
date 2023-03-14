#!/usr/bin/python
# -*- coding: utf-8 -*

import base64
import copy
import json
import os
import requests
import requests_mock
from requests_mock import NoMockAddress
import shutil
import tempfile
import unittest

import pytest
import re

from hamcrest import contains_string

try:
    from unittest.mock import patch, MagicMock
except ImportError:  # pragma: no cover
    from mock import patch, MagicMock
from urllib3.exceptions import MaxRetryError, ResponseError

from pushsource._impl.utils.containers import (
    api_version_check,
    get_manifest,
    inspect,
    MEDIATYPE_SCHEMA2_V1,
    MEDIATYPE_SCHEMA2_V1_SIGNED,
    MEDIATYPE_SCHEMA2_V2,
    MEDIATYPE_SCHEMA2_V2_LIST,
)

from pushsource._impl.utils.containers.request import (
    parse_401_response_headers,
    AuthToken,
    request_token,
)


@pytest.fixture
def fake_home(tmpdir, monkeypatch):
    tmp_home = tmpdir.mkdir("home")
    orig_home = os.environ.get("HOME", "")
    monkeypatch.setenv("HOME", str(tmp_home))
    auth_settings = {
        "auths": {
            "registry.docker.io": {"auth": "cHViOnJlZGhhdA==", "email": ""},
            "test-reqistry.redhat.com": {"auth": "cHViOnJlZGhhdA==", "email": ""},
        }
    }
    tmp_home.mkdir(".docker")
    with open(os.path.join(str(tmp_home), ".docker/config.json"), "w") as f:
        f.write(json.dumps(auth_settings))
        f.close()
    yield tmp_home


def test_need_token_authentication(requests_mock):
    service = "test-registry"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://test-registry.redhat.com/v2/",
        [
            {
                "status_code": 401,
                "headers": {
                    "Www-Authenticate": 'Bearer realm="%s/token",service="%s"'
                    % ("https://auth.test-registry.redhat.com", service)
                },
            },
            {"status_code": 200},
        ],
    )
    requests_mock.register_uri(
        "GET",
        "%s/token?service=%s" % (auth_url, service),
        json={"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1"},
    )
    assert api_version_check("https://test-registry.redhat.com")
    assert [(x.method, x.url) for x in requests_mock.request_history] == [
        ("GET", "https://test-registry.redhat.com/v2/"),
        ("GET", "https://auth.test-registry.redhat.com/token?service=test-registry"),
        ("GET", "https://test-registry.redhat.com/v2/"),
    ]


def test_provided_token_authentication(requests_mock):
    service = "test-registry"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://test-registry.redhat.com/v2/",
        [
            {"status_code": 200},
        ],
    )
    assert api_version_check("https://test-registry.redhat.com", token=AuthToken("123"))
    assert [(x.method, x.url) for x in requests_mock.request_history] == [
        ("GET", "https://test-registry.redhat.com/v2/"),
    ]


def test_need_token_authentication_no_realm(requests_mock):
    service = "test-registry"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://test-registry.redhat.com/v2/",
        [
            {
                "status_code": 401,
                "headers": {"Www-Authenticate": "Bearer"},
            },
            {"status_code": 200},
        ],
    )
    requests_mock.register_uri(
        "GET",
        "%s/token?service=%s" % (auth_url, service),
        json={"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1"},
    )
    with pytest.raises(
        IOError, match=re.escape("No realm specified for token auth challenge.")
    ):
        assert api_version_check("https://test-registry.redhat.com")


def test_need_token_authentication_basic_auth(requests_mock):
    service = "registry.docker.io"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://test-registry.redhat.com/v2/",
        [
            {
                "status_code": 401,
                "headers": {
                    "Www-Authenticate": 'Bearer realm="%s/token",service="%s"'
                    % (auth_url, service)
                },
            },
            {"status_code": 200},
        ],
    )
    requests_mock.register_uri(
        "GET",
        "%s/token?service=%s" % (auth_url, service),
        json={"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1"},
    )
    api_version_check(
        "https://test-registry.redhat.com", credentials=("login", "password")
    )
    assert requests_mock.call_count == 3
    requests_mock.request_history[1].headers[
        "Authorization"
    ] == "Basic bG9naW46cGFzc3dvcmQ="


def test_authentication_basic_auth(requests_mock):
    """For services with just basic auth (docker-pulp) no Bearer tokens
    are emitted. Instead Basic auth is required."""
    service = "registry.docker.io"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/" % service,
        [
            {
                "status_code": 401,
                "headers": {"Www-Authenticate": 'Basic realm="pub-dev-pulp"'},
            },
            {"status_code": 200},
        ],
    )
    requests_mock.register_uri("GET", auth_url)
    assert api_version_check(
        "https://registry.docker.io", credentials=("login", "password")
    )
    assert requests_mock.call_count == 2
    # second request (after failed first) should contain auth headers
    # base64.encode('login:password')
    requests_mock.request_history[1].headers[
        "Authorization"
    ] == "Basic bG9naW46cGFzc3dvcmQ="


def test_api_version_check_404(requests_mock):
    """For services with just basic auth (docker-pulp) no Bearer tokens
    are emitted. Instead Basic auth is required."""
    service = "registry.docker.io"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/" % service,
        [
            {
                "status_code": 404,
            },
        ],
    )
    assert not api_version_check(
        "https://registry.docker.io", credentials=("login", "password")
    )
    assert requests_mock.call_count == 1


def test_api_version_check_unknown_registry_version(requests_mock):
    """For services with just basic auth (docker-pulp) no Bearer tokens
    are emitted. Instead Basic auth is required."""
    service = "registry.docker.io"
    auth_url = "https://auth.test-registry.redhat.com"
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/" % service,
        [
            {
                "status_code": 200,
                "headers": {"Docker-Distribution-API-Version": "registry/3.0"},
            }
        ],
    )
    assert not api_version_check(
        "https://registry.docker.io", credentials=("login", "password")
    )
    assert requests_mock.call_count == 1


def test_get_manifest(requests_mock, fake_home):
    service = "registry.docker.io"
    image = "repo/sitory"
    expected_tag = "latest"
    expected_digest = (
        "sha256:25a01ec9bfd13d405583ef21cdc9ba3182684578ee46248559e75eb59cd73f36"
    )
    expected_manifest = {
        "architecture": "amd64",
        "fsLayers": [
            {
                "blobSum": "sha256:b4a41a81fce32bd7fb00ad10e6c73285f937ce2110a619d306ec09f487b40cca"
            },
            {
                "blobSum": "sha256:16dc1f96e3a1bb628be2e00518fec2bb97bd5933859de592a00e2eb7774b6ecf"
            },
        ],
        "name": "twaugh/buildroot",
        "schemaVersion": 1,
        "signatures": [
            {
                "header": {
                    "alg": "ES256",
                    "jwk": {
                        "crv": "P-256",
                        "kid": "IT3U:4H7H:YPAL:CSU4:CAC2:MFNW:IWV5:YQNM:547A:FMN4:A4D3:UZAG",
                        "kty": "EC",
                        "x": "WjjIX9YwUSO64Zc5iNMODC4mh9vB-mqgt1uEcE7gLfE",
                        "y": "6fhZlalfi9_cvQd-AwBBwGnidIZKIYVzLsSV6HBR8jA",
                    },
                },
                "protected": "eyJmb3JtYXRMZW5ndGgiOjIzMjAsImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAxNi0wNy0xM1QwOToxNjoxMFoifQ",
                "signature": "-dqrUzJ8IbSURO__gkbG2vdzQEbjX32Qv2DjWG3mazTGsRXXgYofr-6VY7lMDUwiOERTD9Te9wyyrALMB7Yt1A",
            }
        ],
        "tag": expected_tag,
    }

    headers = {
        "docker-content-digest": expected_digest,
        "content-type": "application/vnd.docker.distribution.manifest.v1+json",
    }
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (service, image, expected_tag),
        status_code=200,
        headers=headers,
        json=expected_manifest,
    )

    _, actual_digest, actual_manifest = get_manifest(
        "https://%s" % service, image, expected_tag
    )
    assert expected_digest == actual_digest
    assert expected_manifest == actual_manifest


@pytest.mark.parametrize(
    "expected_manifest,manifest_type,accept_types, default_should_raise",
    [
        (
            {"dummy": "manifest v1"},
            MEDIATYPE_SCHEMA2_V1,
            [MEDIATYPE_SCHEMA2_V1, MEDIATYPE_SCHEMA2_V1_SIGNED],
            False,
        ),
        ({"dummy": "manifest v1"}, MEDIATYPE_SCHEMA2_V1, [], False),
        ({"dummy": "manifest v2"}, MEDIATYPE_SCHEMA2_V2, [MEDIATYPE_SCHEMA2_V2], True),
        (
            {"dummy": "manifest list"},
            MEDIATYPE_SCHEMA2_V2_LIST,
            [MEDIATYPE_SCHEMA2_V2_LIST],
            True,
        ),
    ],
)
def test_get_manifest_default(
    expected_manifest,
    manifest_type,
    accept_types,
    default_should_raise,
    requests_mock,
    fake_home,
):
    service = "registry.docker.io"
    image = "repo/sitory"
    expected_tag = "latest"
    expected_digest = "sha256:dummy_digest"
    # return manifest type depending on Content-Type header

    headers = {"docker-content-digest": expected_digest}
    if manifest_type:
        headers["content-type"] = manifest_type
    request_headers = {}
    if accept_types:
        request_headers = {"Accept": ",".join(accept_types)}
    requests_mock.get(  # nosec B113
        "https://%s/v2/%s/manifests/%s" % (service, image, expected_tag),
        status_code=200,
        headers=headers,
        request_headers=request_headers,
        json=expected_manifest,
    )

    # test default
    if default_should_raise:
        with pytest.raises(NoMockAddress):
            _, actual_digest, actual_manifest = get_manifest(
                "https://%s" % service, image, expected_tag
            )
    else:
        _, actual_digest, actual_manifest = get_manifest(
            "https://%s" % service, image, expected_tag
        )
        assert expected_digest == actual_digest
        assert expected_manifest == actual_manifest

    # test required
    _, actual_digest, actual_manifest = get_manifest(
        "https://%s" % service, image, expected_tag, manifest_types=accept_types
    )
    assert expected_digest == actual_digest
    assert expected_manifest == actual_manifest


def test_get_manifest_raise_on_500(requests_mock, fake_home):
    tag = "latest"
    image = "repo/sitory"
    service = "registry.docker.io"
    requests_mock.register_uri(
        "GET", "https://%s/v2/%s/manifests/%s" % (service, image, tag), status_code=500
    )

    with pytest.raises(requests.exceptions.HTTPError, match="500 Server Error: None"):
        _, digest, manifest = get_manifest("https://registry.docker.io", image, tag)


def test_get_manifest_raise_on_404(requests_mock, fake_home):
    # when there is no API endpoint found, regular 404 should be raised.
    # It is the difference to correct API-returned 404 which contains
    # json data about errors
    # (test_get_manifest_raise_on_UNKNOWN_MANIFEST)
    tag = "latest"
    image = "repo/sitory"
    service = "registry.docker.io"

    requests_mock.register_uri(
        "GET", "https://%s/v2/%s/manifests/%s" % (service, image, tag), status_code=404
    )

    with pytest.raises(requests.exceptions.HTTPError, match="404 Client Error: None"):
        _, digest, manifest = get_manifest("https://%s" % service, image, tag)


def test_get_manifest_raise_on_UNKNOWN_MANIFEST(requests_mock, fake_home):
    tag = "latest"
    image = "repo/sitory"
    service = "registry.docker.io"

    error_message = re.escape(
        "\"Failed to get the manifest for image 'repo/sitory' [latest]\""
    )
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (service, image, tag),
        status_code=404,
        json={"errors": [{"code": "MANIFEST_UNKNOWN"}]},
    )

    with pytest.raises(KeyError, match=error_message):
        digest, manifest = get_manifest("https://%s" % service, image, tag)


def test_request_token_without_scope(requests_mock):
    image = "repo/sitory"
    service = "registry.docker.io"
    expected_token = "new token"
    headers = {
        "www-authenticate": 'Bearer realm="https://{0}/token",service="registry.docker.io"'.format(
            service
        )
    }
    response = MagicMock(headers=headers)

    def call_back(request, context):
        if request.path_url.find("scope=") >= 0:
            context.__setattr__("status_code", 200),
            return {"token": expected_token}
        else:
            context.__setattr__("status_code", 401),
            context.__setattr__("reason", "Unauthorized access"),
            return {}

    requests_mock.register_uri(
        "GET",
        "https://%s/token" % (service,),
        json=call_back,
    )

    token = request_token(
        requests.session(),
        response=response,
        credentials=("user", "pass"),
        repo_name=image,
    )

    assert token == expected_token


def test_request_token_only_if_requested_by_server(requests_mock):
    tag = "latest"
    image = "repo/sitory"
    service = "registry.docker.io"
    # If basic authentication fails and no bear authentication is requested by server
    # then fail immediately
    requests_mock.register_uri(
        "GET", "https://%s/v2/" % service, status_code=401, reason="Unauthorized access"
    )
    with pytest.raises(
        requests.exceptions.HTTPError, match="401 Client Error: Unauthorized access"
    ):
        api_version_check("https://%s" % service, credentials=("user", "pass"))


def test_parse_401_response_headers_valid():
    tests = (
        (
            # everything in quotes
            'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",scope="repository:library/nginx:pull,push"',
            {
                "realm": "https://auth.docker.io/token",
                "service": "registry.docker.io",
                "scope": "repository:library/nginx:pull,push",
            },
        ),
        (
            # everything without quotes
            "Bearer realm=https://auth.docker.io/token,service=registry.docker.io,scope=repository:library/nginx:pull",
            {
                "realm": "https://auth.docker.io/token",
                "service": "registry.docker.io",
                "scope": "repository:library/nginx:pull",
            },
        ),
        (
            # mixed content
            'Bearer realm=https://auth.docker.io/token,service=registry.docker.io,scope="repository:library/nginx:pull,push"',
            {
                "realm": "https://auth.docker.io/token",
                "service": "registry.docker.io",
                "scope": "repository:library/nginx:pull,push",
            },
        ),
    )

    # valid headers
    for src, dst in tests:
        headers = {"www-authenticate": src}
        ret = parse_401_response_headers(headers)
        assert dst == ret


def test_parse_401_response_headers_missing():
    with pytest.raises(IOError):
        parse_401_response_headers({})


def test_parse_401_response_headers_invalid():
    headers = {"www-authenticate": "This is not bearer header"}
    with pytest.raises(IOError):
        parse_401_response_headers(headers)


def test_inspect_v1(requests_mock):
    registry = "fake-registry"
    repo = "test-repo"
    tag = "test-tag"
    headers = {
        "docker-content-digest": "test-digest",
        "content-type": "application/vnd.docker.distribution.manifest.v1+json",
    }
    expected_manifest = {
        "architecture": "amd64",
        "fsLayers": [
            {
                "blobSum": "sha256:b4a41a81fce32bd7fb00ad10e6c73285f937ce2110a619d306ec09f487b40cca"
            },
            {
                "blobSum": "sha256:16dc1f96e3a1bb628be2e00518fec2bb97bd5933859de592a00e2eb7774b6ecf"
            },
        ],
        "name": "twaugh/buildroot",
        "schemaVersion": 1,
        "signatures": [
            {
                "header": {
                    "alg": "ES256",
                    "jwk": {
                        "crv": "P-256",
                        "kid": "IT3U:4H7H:YPAL:CSU4:CAC2:MFNW:IWV5:YQNM:547A:FMN4:A4D3:UZAG",
                        "kty": "EC",
                        "x": "WjjIX9YwUSO64Zc5iNMODC4mh9vB-mqgt1uEcE7gLfE",
                        "y": "6fhZlalfi9_cvQd-AwBBwGnidIZKIYVzLsSV6HBR8jA",
                    },
                },
                "protected": "eyJmb3JtYXRMZW5ndGgiOjIzMjAsImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAxNi0wNy0xM1QwOToxNjoxMFoifQ",
                "signature": "-dqrUzJ8IbSURO__gkbG2vdzQEbjX32Qv2DjWG3mazTGsRXXgYofr-6VY7lMDUwiOERTD9Te9wyyrALMB7Yt1A",
            }
        ],
        "tag": tag,
    }
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (registry, repo, tag),
        status_code=200,
        headers=headers,
        json=expected_manifest,
    )
    inspected = inspect("https://fake-registry", "test-repo", "test-tag")
    assert inspected == {
        "architecture": "amd64",
        "config": {"Labels": {}},
        "digest": "test-digest",
    }


def test_inspect_v2(requests_mock):
    registry = "fake-registry"
    repo = "test-repo"
    tag = "test-tag"
    expected_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 20150,
            "digest": "sha256:adb48f5d2b45131f87a2c52a791e08185769c9f9018f7e63b760dcb4f188bd13",
        },
        "layers": [],
    }
    expected_blob = {
        "architecture": "ppc64le",
        "config": {
            "Labels": {
                "architecture": "ppc64le",
            }
        },
    }
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (registry, repo, tag),
        json=lambda req, context: [
            context.__setattr__("status_code", 200),
            context.__setattr__(
                "headers",
                {
                    "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
                    "docker-content-digest": "test-digest",
                },
            ),
            expected_manifest,
        ][-1],
    )
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/blobs/%s"
        % (
            registry,
            repo,
            "sha256:adb48f5d2b45131f87a2c52a791e08185769c9f9018f7e63b760dcb4f188bd13",
        ),
        status_code=200,
        json=expected_blob,
    )
    inspected = inspect("https://%s" % registry, "test-repo", "test-tag")
    assert inspected == {
        "architecture": "ppc64le",
        "config": {"Labels": {"architecture": "ppc64le"}},
        "digest": "test-digest",
    }


def test_inspect_list(requests_mock):
    registry = "fake-registry"
    repo = "test-repo"
    tag = "test-tag"
    expected_manifest_list = {
        "manifests": [
            {
                "digest": "sha256:e7e5d23bcb765d71604755e93bd32c4dc3df1d1588948f3039e473fff4d4ced8",
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "platform": {"architecture": "amd64", "os": "linux"},
                "size": 1161,
            },
            {
                "digest": "sha256:7302dbd6e274f154b47f04208d756d2c42fa167787f74de67516765eb8e06e38",
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "platform": {"architecture": "ppc64le", "os": "linux"},
                "size": 1161,
            },
        ],
        "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
        "schemaVersion": 2,
    }
    expected_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 6069,
            "digest": "sha256:7a37792a49b36c89d4f196dbebd03ffe4c85ccf36d357234418a5b9fc8b5e939",
        },
    }
    expected_blob = {
        "architecture": "ppc64le",
        "config": {
            "Labels": {
                "architecture": "ppc64le",
            }
        },
    }
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (registry, repo, tag),
        content=lambda req, context: [
            context.__setattr__("status_code", 200),
            context.__setattr__(
                "headers",
                {
                    "Content-Type": "application/vnd.docker.distribution.manifest.list.v2+json",
                },
            ),
            json.dumps(expected_manifest_list, sort_keys=True).encode("utf-8"),
        ][-1],
    )
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s"
        % (
            registry,
            repo,
            "sha256:e7e5d23bcb765d71604755e93bd32c4dc3df1d1588948f3039e473fff4d4ced8",
        ),
        content=lambda req, context: [
            context.__setattr__("status_code", 200),
            context.__setattr__(
                "headers",
                {
                    "Content-Type": "application/vnd.docker.distribution.manifest.list.v2+json",
                    "docker-content-digest": "sha256:e7e5d23bcb765d71604755e93bd32c4dc3df1d1588948f3039e473fff4d4ced8",
                },
            ),
            json.dumps(expected_manifest, sort_keys=True).encode("utf-8"),
        ][-1],
    )
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/blobs/%s"
        % (
            registry,
            repo,
            "sha256:7a37792a49b36c89d4f196dbebd03ffe4c85ccf36d357234418a5b9fc8b5e939",
        ),
        status_code=200,
        json=expected_blob,
    )
    inspected = inspect("https://%s" % registry, "test-repo", "test-tag")
    assert inspected == {
        "architecture": "ppc64le",
        "config": {"Labels": {"architecture": "ppc64le"}},
        # digest should be calculated from manifest list
        "digest": "sha256:1e89f8bff8d8a6c324ed32ff35ecd457aefec17be856f6bb3a868c2a394dcc88",
    }


def test_inspect_source(requests_mock):
    registry = "fake-registry"
    repo = "test-repo"
    tag = "test-tag"
    expected_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 20150,
            "digest": "sha256:adb48f5d2b45131f87a2c52a791e08185769c9f9018f7e63b760dcb4f188bd13",
        },
        "layers": [],
    }
    expected_blob = {"architecture": "ppc64le", "config": {"Labels": {}}}
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/manifests/%s" % (registry, repo, tag),
        json=lambda req, context: [
            context.__setattr__("status_code", 200),
            context.__setattr__(
                "headers",
                {
                    "Content-Type": "application/vnd.docker.distribution.manifest.v2+json",
                    "docker-content-digest": "test-digest",
                },
            ),
            expected_manifest,
        ][-1],
    )
    requests_mock.register_uri(
        "GET",
        "https://%s/v2/%s/blobs/%s"
        % (
            registry,
            repo,
            "sha256:adb48f5d2b45131f87a2c52a791e08185769c9f9018f7e63b760dcb4f188bd13",
        ),
        status_code=200,
        json=expected_blob,
    )
    inspected = inspect("https://%s" % registry, "test-repo", "test-tag")
    assert inspected == {
        "architecture": "ppc64le",
        "config": {"Labels": {}},
        "digest": "test-digest",
        "source": True,
    }
