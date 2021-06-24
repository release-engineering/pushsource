# Helpers for dealing with container metadata from koji.

from ..model import ContainerImagePullSpec, ContainerImagePullInfo
from .. import compat_attr as attr

MIME_TYPE_MANIFEST_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"


class ContainerArchiveHelper(object):
    def __init__(self, build, archive):
        self._build = build
        self._archive = archive

    @property
    def build_image(self):
        extra = self._build.get("extra") or {}
        typeinfo = extra.get("typeinfo") or {}
        # It is preferred to use the metadata under 'typeinfo' if present
        return typeinfo.get("image") or extra.get("image") or {}

    @property
    def build_index(self):
        return self.build_image.get("index") or {}

    @property
    def archive_extra(self):
        return self._archive.get("extra") or {}

    @property
    def archive_docker(self):
        return self.archive_extra.get("docker") or {}

    @property
    def source_tags(self):
        return self.archive_docker.get("tags") or []

    @property
    def arch(self):
        config = self.archive_docker.get("config") or {}
        image = self.archive_extra.get("image") or {}

        out = config.get("architecture")

        if not out:
            # Ideally we got the arch from 'config' which will use the
            # docker-native arch strings. For ancient/weird builds we may
            # have had to fall back to 'image'.
            out = image.get("arch")

            # In this case, we get koji's native arch strings instead
            # which can be different. Convert them to the terms used in
            # the container world so we get consistent output.
            archmap = {"x86_64": "amd64", "aarch64": "arm64"}
            out = archmap.get(out, out)

        return out

    @property
    def labels(self):
        out = {}

        config = self.archive_docker.get("config") or {}
        # yes, config.config is the expected structure
        config = config.get("config") or {}
        raw_labels = config.get("Labels") or {}

        # We are going to be a bit selective with the labels we return.
        # The reason for this is just to keep a higher level of control
        # over the data we produce. Labels include all sorts of random
        # stuff and it'd be best not to use them in some cases and instead
        # require proper fields to be added onto our models.
        #
        # "com.redhat." is permitted because fields in that namespace are
        # known to be required for some operator images, e.g.
        # com.redhat.openshift.versions documented at
        # https://redhat-connect.gitbook.io/certified-operator-guide/ocp-deployment/operator-metadata/bundle-directory
        # which has its own non-trivial syntax we don't want to get into parsing.
        for (key, value) in raw_labels.items():
            if key.startswith("com.redhat."):
                out[key] = value

        return out

    @property
    def pull_info(self):
        ################## Image pull specs - from archive ##############################
        # Get image pull info from archive.
        archive_raw_specs = self.archive_docker.get("repositories") or []
        archive_digests = self.archive_docker.get("digests") or {}
        image_digest_specs = get_digest_specs(archive_raw_specs, archive_digests)
        image_tag_specs = get_tag_specs(archive_raw_specs)

        ################## List pull specs - from build #################################
        build_raw_specs = self.build_index.get("pull") or {}
        build_digests = self.build_index.get("digests") or {}
        list_digest_specs = get_digest_specs(build_raw_specs, build_digests)
        list_tag_specs = get_tag_specs(build_raw_specs)

        # Metadata does not explicitly tell us the media type per tag, but these tag
        # specs are known to be for manifest lists. We'll sanity check that this type
        # is present in the digests map at least.
        if MIME_TYPE_MANIFEST_LIST in build_digests:
            list_tag_specs = [
                attr.evolve(spec, media_types=[MIME_TYPE_MANIFEST_LIST])
                for spec in list_tag_specs
            ]

        ################### Put it all together #######################################
        # Note: ContainerimagePullInfo itself performs various operations on these specs
        # such as sorting and de-duplication.
        return ContainerImagePullInfo(
            tag_specs=list_tag_specs + image_tag_specs,
            digest_specs=list_digest_specs + image_digest_specs,
        )


def get_tag_specs(raw_specs):
    return [ContainerImagePullSpec._from_str(s) for s in raw_specs if "@" not in s]


def get_digest_specs(raw_specs, digests_map):
    out = []

    # Reverse the type => digest map
    digest_to_type = {}
    for (media_type, digest) in digests_map.items():
        digest_to_type[digest] = media_type

    for raw_spec in raw_specs:
        if "@" not in raw_spec:
            continue

        # raw_spec is a value such as:
        # registry-proxy.engineering.redhat.com/rh-osbs/openshift3-ose-logging-elasticsearch5@sha256:14f09792420665534c9d66ee3d055ff5b78d95e736c4a9fc8172cc01ecf39598
        spec = ContainerImagePullSpec._from_str(raw_spec)

        # If we know the specific type of this digest, add it.
        # (It's only ancient builds where we won't know.)
        spec = attr.evolve(spec, media_type=digest_to_type.get(spec.digest))

        out.append(spec)

    return out
