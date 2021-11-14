import re
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

IMAGE_URI_REGEX = re.compile("https://([^:@]*):(.+)(([^:]:)+)*")


class RegistrySource(Source):
    """Uses a container image registry as a source of push items."""

    def __init__(self, image, dest=None, dest_signing_key=None):
        """Create a new source.

        Parameters:
            image (str, list[str])
                Pull spec(s) of container images, as a list or a comma-separated string.

                Each pull spec must include a hostname and a tag; referencing images by digest
                is currently not supported.

                ``registry.access.redhat.com/ubi8/ubi:8.4-211`` is an example of a valid pull
                spec.

            dest (str, list[str])
                If provided, this value will be used to populate :meth:`~pushsource.PushItem.dest`
                on generated push items.

            dest_signing_key (str, list[str])
                If provided, this value will be used to populate
                :meth:`~pushsource.ContainerImagePushItem.dest_signing_key` on generated
                push items.

                Note that, as each item holds only a single ``dest_signing_key``, using this
                argument can affect the number of generated push items. For example,
                providing two keys would produce double the amount of push items as providing
                a single key.
        """
        self._images = ["https://%s" % x for x in list_argument(image)]
        if dest:
            self._repos = list_argument(dest)
        else:
            self._repos = []
        self._signing_keys = list_argument(dest_signing_key)
        self._inspected = {}
        self._manifests = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _push_item_from_registry_uri(self, uri, signing_key):
        if not IMAGE_URI_REGEX.match(uri):
            raise ValueError(
                "Invalid item uri: %s. Please use format: %s"
                % (uri, IMAGE_URI_REGEX.pattern)
            )

        schema, rest = uri.split("://")
        host, rest = rest.split("/", 1)
        repo, src_tag = rest.split(":", 1)
        source_uri = "%s/%s:%s" % (host, repo, src_tag)
        if source_uri not in self._inspected:
            self._inspected[source_uri] = inspect(
                "%s://%s" % (schema, host), repo, src_tag
            )
        if self._inspected[source_uri].get("source"):
            klass = SourceContainerImagePushItem
        else:
            klass = ContainerImagePushItem

        if source_uri not in self._manifests:
            manifest_details = get_manifest(
                "%s://%s" % (schema, host),
                repo,
                src_tag,
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
                    digest=self._inspected.get(source_uri, {}).get("digest"),
                    media_type=content_type,
                )
            ],
            media_types=[content_type],
            tag_specs=[
                ContainerImageTagPullSpec(
                    registry=host,
                    repository=repo,
                    tag=src_tag,
                    media_types=[content_type],
                )
            ],
        )
        return klass(
            name=source_uri,
            dest=self._repos,
            dest_signing_key=signing_key,
            src=source_uri,
            source_tags=[src_tag],
            labels=self._inspected.get(source_uri, {}).get("config").get("Labels", {}),
            arch=(self._inspected.get(source_uri, {}).get("config", {}) or {})
            .get("Labels", {})
            .get("Labels", {})
            .get("architecture"),
            pull_info=pull_info,
        )

    def __iter__(self):
        for key in self._signing_keys or [None]:
            for uri in self._images:
                yield self._push_item_from_registry_uri(uri, key)


Source._register_backend_builtin("registry", RegistrySource)
