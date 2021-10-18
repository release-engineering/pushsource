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
import six

from hamcrest import contains_string

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock
from urllib3.exceptions import MaxRetryError, ResponseError

from pushsource._impl.utils.containers import (
    api_version_check,
    get_manifest,
    MT_S2_V1,
    MT_S2_V1_SIGNED,
    MT_S2_V2,
    MT_S2_LIST,
)

from pushsource._impl.utils.containers.request import (
    parse_401_response_headers,
    AuthToken,
)


@pytest.fixture
def fake_home():
    tmp_home = None
    try:
        tmp_home = tempfile.mkdtemp()
        orig_home = os.environ.get("HOME", "")
        os.environ["HOME"] = tmp_home
        auth_settings = {
            "auths": {
                "registry.docker.io": {"auth": "cHViOnJlZGhhdA==", "email": ""},
                "test-reqistry.redhat.com": {"auth": "cHViOnJlZGhhdA==", "email": ""},
            }
        }
        os.mkdir(os.path.join(tmp_home, ".docker"))
        with open(os.path.join(tmp_home, ".docker/config.json"), "w") as f:
            f.write(json.dumps(auth_settings))
            f.close()
            yield tmp_home
    finally:
        if tmp_home:
            shutil.rmtree(tmp_home)
    os.environ["HOME"] = orig_home


@pytest.fixture
def fake_home_no_auths():
    with tempfile.TemporaryDirectory() as tmp_home:
        orig_home = os.environ.get("HOME", "")
        os.environ["HOME"] = tmp_home
        auth_settings = {"auths": {}}
        os.mkdir(os.path.join(tmp_home, ".docker"))
        with open(os.path.join(tmp_home, ".docker/config.json"), "w") as f:
            f.write(json.dumps(auth_settings))
            f.close()
            yield tmp_home
    os.environ["HOME"] = orig_home


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
        u"architecture": u"amd64",
        u"fsLayers": [
            {
                u"blobSum": u"sha256:b4a41a81fce32bd7fb00ad10e6c73285f937ce2110a619d306ec09f487b40cca"
            },
            {
                u"blobSum": u"sha256:16dc1f96e3a1bb628be2e00518fec2bb97bd5933859de592a00e2eb7774b6ecf"
            },
        ],
        u"name": u"twaugh/buildroot",
        u"schemaVersion": 1,
        u"signatures": [
            {
                u"header": {
                    u"alg": u"ES256",
                    u"jwk": {
                        u"crv": u"P-256",
                        u"kid": u"IT3U:4H7H:YPAL:CSU4:CAC2:MFNW:IWV5:YQNM:547A:FMN4:A4D3:UZAG",
                        u"kty": u"EC",
                        u"x": u"WjjIX9YwUSO64Zc5iNMODC4mh9vB-mqgt1uEcE7gLfE",
                        u"y": u"6fhZlalfi9_cvQd-AwBBwGnidIZKIYVzLsSV6HBR8jA",
                    },
                },
                u"protected": u"eyJmb3JtYXRMZW5ndGgiOjIzMjAsImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAxNi0wNy0xM1QwOToxNjoxMFoifQ",
                u"signature": u"-dqrUzJ8IbSURO__gkbG2vdzQEbjX32Qv2DjWG3mazTGsRXXgYofr-6VY7lMDUwiOERTD9Te9wyyrALMB7Yt1A",
            }
        ],
        u"tag": expected_tag,
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
        ({"dummy": "manifest v1"}, MT_S2_V1, [MT_S2_V1, MT_S2_V1_SIGNED], False),
        ({"dummy": "manifest v1"}, MT_S2_V1, [], False),
        ({"dummy": "manifest v2"}, MT_S2_V2, [MT_S2_V2], True),
        ({"dummy": "manifest list"}, MT_S2_LIST, [MT_S2_LIST], True),
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
    requests_mock.get(
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
