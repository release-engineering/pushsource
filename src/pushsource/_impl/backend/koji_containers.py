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
        return self.archive_docker.get("tags")

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
