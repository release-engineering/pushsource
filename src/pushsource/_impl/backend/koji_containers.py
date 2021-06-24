# Helpers for dealing with container metadata from koji.


class ContainerArchiveHelper(object):
    def __init__(self, archive):
        self._archive = archive

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
