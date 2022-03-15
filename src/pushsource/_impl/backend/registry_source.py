import re
import logging

import requests

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
    MEDIATYPE_SCHEMA2_V2,
    MEDIATYPE_SCHEMA2_V1,
    MEDIATYPE_SCHEMA2_V1_SIGNED,
    MEDIATYPE_SCHEMA2_V2_LIST,
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

        for mtype in [
            MEDIATYPE_SCHEMA2_V1,
            MEDIATYPE_SCHEMA2_V2,
            MEDIATYPE_SCHEMA2_V2_LIST,
        ]:
            if source_uri not in self._manifests:
                self._manifests[source_uri] = {}
            if mtype not in self._manifests[source_uri]:
                try:
                    manifest_details = get_manifest(
                        "%s://%s" % (schema, host),
                        repo,
                        src_tag,
                        manifest_types=[mtype],
                    )
                    self._manifests[source_uri][mtype] = manifest_details
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        continue
                    raise e

            manifest_details = self._manifests[source_uri][mtype]
            content_type, _, _ = manifest_details
            # tolerate text/plain as MEDIATYPE_SCHEMA2_V1 (due to wrong configuration in CDN)
            if content_type not in [
                MEDIATYPE_SCHEMA2_V2,
                MEDIATYPE_SCHEMA2_V1,
                MEDIATYPE_SCHEMA2_V1_SIGNED,
                MEDIATYPE_SCHEMA2_V2_LIST,
                "text/plain",
            ]:
                raise ValueError("Unsupported manifest type: %s" % content_type)

        pull_info = ContainerImagePullInfo(
            digest_specs=[
                ContainerImageDigestPullSpec(
                    registry=host,
                    repository=repo,
                    digest=manifest[1],
                    # replace text/plain with correct value
                    media_type=manifest[0].replace("text/plain", MEDIATYPE_SCHEMA2_V1),
                )
                for manifest in self._manifests[source_uri].values()
            ],
            media_types=list(
                set(
                    [
                        manifest[0].replace("text/plain", MEDIATYPE_SCHEMA2_V1)
                        for manifest in self._manifests[source_uri].values()
                    ]
                )
            ),
            tag_specs=[
                ContainerImageTagPullSpec(
                    registry=host,
                    repository=repo,
                    tag=src_tag,
                    media_types=list(
                        set(
                            [
                                manifest[0].replace("text/plain", MEDIATYPE_SCHEMA2_V1)
                                for manifest in self._manifests[source_uri].values()
                            ]
                        )
                    ),
                )
            ],
        )
        # manifest list or v2 sch1
        labels = self._inspected.get(source_uri, {}).get("config").get(
            "Labels", {}
        ) or self._inspected.get(source_uri, {}).get("labels", {})
        arch = labels.get("architecture")

        return klass(
            name=source_uri,
            dest=self._repos,
            dest_signing_key=signing_key,
            src=source_uri,
            source_tags=[src_tag],
            labels=labels,
            arch=arch,
            pull_info=pull_info,
        )

    def __iter__(self):
        for key in self._signing_keys or [None]:
            for uri in self._images:
                yield self._push_item_from_registry_uri(uri, key)


Source.register_backend("registry", RegistrySource)
