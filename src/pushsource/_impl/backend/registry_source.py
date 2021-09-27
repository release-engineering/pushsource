import logging


try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from ..source import Source
from ..model import (
    ContainerImagePushItem,
    SourceContainerImagePushItem,
    ContainerImagePullInfo,
    ContainerImageTagPullSpec,
    ContainerImageDigestPullSpec,
)
from ..utils.executor.skopeo import SkopeoContainerExecutor
from ..utils.containers import (
    get_manifest,
    MT_S2_V2,
    MT_S2_V1,
    MT_S2_V1_SIGNED,
    MT_S2_LIST,
)

from ..helpers import list_argument

LOG = logging.getLogger("pushsource")


class RegistrySource(Source):
    """Uses URIs of container images as source for push items."""

    def __init__(
        self,
        dest=None,
        registry_uris=None,
        signing_key=None,
        docker_url="unix://var/run/docker.sock",
        executor_container_image=None,
        docker_timeout=None,
        docker_verify_tls=None,
        docker_cert_path=None,
    ):
        """Create a new source.

        Parameters:
            dest (str, list[str])
                The destination(s) to fill in for push items created by this
                source. If omitted, all push items have empty destinations.

            registry_uris (list[str])
                List of references to container images with tags

            signing_key (list[str])
                GPG signing key ID(s). If provided, content must be signed
                using one of the provided keys. Include ``None`` if unsigned
                should also be permitted.
                Keys should be listed in the order of preference.

            executor_container_image (str):
                Path to the container image in which to execute the commands. Must be downloadable
                without extra permissions.

            docker_url (str):
                URL of the docker client that should run the container. Local socket by default.

            docker_timeout (int):
                Timeout for executing Docker commands. Disabled by default.

            docker_verify_tls (bool):
                Whether to perform TLS verification with the Docker client. Disabled by default.

            docker_cert_path (str):
                Path to Docker certificates for TLS authentication. '~/.docker' by default.
        """
        self._registry_uris = registry_uris
        self._dest = list_argument(dest)
        self.signing_keys = list_argument(signing_key)
        self.executor_container_image = executor_container_image
        self.docker_url = docker_url
        self.docker_timeout = docker_timeout
        self.docker_verify_tls = docker_verify_tls
        self.docker_cert_path = docker_cert_path
        self.inspected = {}
        self.manifests = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _push_item_from_registry_uri(self, skopeo, uri, signing_key):
        if uri not in self.inspected:
            self.inspected[uri] = inspected = skopeo.commands.skopeo_inspect(uri)
        inspected = self.inspected[uri]

        if (inspected.get("Labels", {}) or {}).get("architecture", "src") != "src":
            klass = ContainerImagePushItem
        else:
            klass = SourceContainerImagePushItem

        parsed = urlparse(uri)
        repo, tag = parsed.path.split(":")
        if uri not in self.manifests:
            manifest_details = get_manifest(
                "%s://%s" % (parsed.scheme, parsed.netloc),
                repo,
                tag,
                manifest_types=[MT_S2_LIST],
            )
            self.manifests[uri] = manifest_details
        manifest_details = self.manifests[uri]
        content_type, _, _ = manifest_details
        if content_type not in [MT_S2_V2, MT_S2_V1, MT_S2_V1_SIGNED, MT_S2_LIST]:
            raise ValueError("Unsupported manifest type:%s" % content_type)

        pull_info = ContainerImagePullInfo(
            digest_specs=[
                ContainerImageDigestPullSpec(
                    registry=parsed.netloc,
                    repository=repo,
                    digest=inspected["Digest"],
                    media_type=content_type,
                )
            ],
            media_types=[content_type],
            tag_specs=[
                ContainerImageTagPullSpec(
                    registry=parsed.netloc,
                    repository=repo,
                    tag=inspected["RepoTags"][0],
                    media_types=[content_type],
                )
            ],
        )

        return klass(
            name=uri,
            dest=self._dest,
            dest_signing_key=signing_key,
            src=uri,
            source_tags=inspected["RepoTags"],
            labels=inspected["Labels"],
            arch=(inspected.get("Labels", {}) or {}).get("architecture"),
            pull_info=pull_info,
        )

    def __iter__(self):
        skopeo = SkopeoContainerExecutor(
            self.executor_container_image,
            self.docker_url,
            self.docker_timeout,
            self.docker_verify_tls,
            self.docker_cert_path,
        )

        for key in self.signing_keys:
            for uri in self._registry_uris:
                yield self._push_item_from_registry_uri(skopeo, uri, key)


Source._register_backend_builtin("registry", RegistrySource)
