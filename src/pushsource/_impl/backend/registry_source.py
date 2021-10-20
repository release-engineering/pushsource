import logging

from ..source import Source
from ..model import (
    ContainerImagePushItem,
    SourceContainerImagePushItem,
    ContainerImagePullInfo,
    ContainerImageTagPullSpec,
    ContainerImageDigestPullSpec,
)
from ..utils.containers import (
    get_manifest,
    inspect,
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
        images_str,
        dest_repos=None,
        dest_signing_key=None,
    ):
        """Create a new source.

        Parameters:
            dest_repos str,
                Comma separated string with destination(s) repo(s) to fill in for push
                items created by this source. If omitted, all push items have
                empty destinations.

            images_str (list[str])
                String with references to container images with tags+dest tags
                Format <scheme>:<host>/<namespace>/<repo>:<tag>:<destination_tag>:<destination_tag>
                Example: https:registry.redhat.io/ubi:8:latest:8:8.1

            signing_key (list[str])
                GPG signing key ID(s). If provided, content must be signed
                using one of the provided keys. Include ``None`` if unsigned
                should also be permitted.
                Keys should be listed in the order of preference.
        """
        self._images = [
            "%s://%s" % tuple(x.split(":", 1)) for x in images_str.split(",")
        ]
        self._dest_repos = dest_repos.split(",")
        print(self._dest_repos)
        self._signing_keys = list_argument(dest_signing_key)
        self._inspected = {}
        self._manifests = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _push_item_from_registry_uri(self, uri, signing_key):
        schema, rest = uri.split("://")
        host, rest = rest.split("/", 1)
        repo, tags_part = rest.split(":", 1)
        tags = tags_part.split(":")
        source_tag = tags[0]
        dest_tags = tags[1:]
        if not dest_tags:
            raise ValueError("At least one dest tag is required for: %s" % uri)
        source_uri = "%s/%s:%s" % (host, repo, source_tag)
        if source_uri not in self._inspected:
            self._inspected[source_uri] = inspect(
                "%s://%s" % (schema, host), repo, source_tag
            )
        if self._inspected[source_uri].get("source"):
            klass = SourceContainerImagePushItem
        else:
            klass = ContainerImagePushItem

        if source_uri not in self._manifests:
            manifest_details = get_manifest(
                "%s://%s" % (schema, host),
                repo,
                source_tag,
                manifest_types=[MT_S2_LIST],
            )
            self._manifests[source_uri] = manifest_details
        manifest_details = self._manifests[source_uri]
        content_type, _, _ = manifest_details
        if content_type not in [MT_S2_V2, MT_S2_V1, MT_S2_V1_SIGNED, MT_S2_LIST]:
            raise ValueError("Unsupported manifest type:%s" % content_type)

        pull_info = ContainerImagePullInfo(
            digest_specs=[
                ContainerImageDigestPullSpec(
                    registry=host,
                    repository=repo,
                    digest=self._inspected[source_uri]["digest"],
                    media_type=content_type,
                )
            ],
            media_types=[content_type],
            tag_specs=[
                ContainerImageTagPullSpec(
                    registry=host,
                    repository=repo,
                    tag=source_tag,
                    media_types=[content_type],
                )
            ],
        )
        item_dests = []
        for dest_repo in self._dest_repos:
            for dest_tag in dest_tags:
                item_dests.append("%s:%s" % (dest_repo, dest_tag))

        return klass(
            name=source_uri,
            dest=item_dests,
            dest_signing_key=signing_key,
            src=source_uri,
            source_tags=[source_tag],
            labels=self._inspected[source_uri].get("config").get("labels", {}),
            arch=(self._inspected[source_uri].get("config", {}) or {})
            .get("labels", {})
            .get("architecture"),
            pull_info=pull_info,
        )

    def __iter__(self):
        for key in self._signing_keys:
            for uri in self._images:
                yield self._push_item_from_registry_uri(uri, key)


Source._register_backend_builtin("registry", RegistrySource)
