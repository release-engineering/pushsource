# Utilities for dealing with modulemd files from backends.
# None of this is public API.
import yaml

from .. import compat_attr as attr


@attr.s()
class Module(object):
    MOD_NSVCA_FMT = "{name}:{stream}:{version}:{context}:{arch}"

    name = attr.ib()
    stream = attr.ib()
    version = attr.ib()
    context = attr.ib()
    arch = attr.ib()

    @property
    def nsvca(self):
        return self.MOD_NSVCA_FMT.format(
            name=self.name,
            stream=self.stream,
            version=self.version,
            context=self.context,
            arch=self.arch,
        )

    @classmethod
    def from_file(cls, fname):
        # Obtain a Module instance from a YAML file.
        # Raises if file doesn't contain a module or has multiple documents.
        with open(fname) as f:
            parsed = yaml.load(f, Loader=yaml.BaseLoader)
        data = parsed["data"]

        return cls(
            name=data["name"],
            stream=data["stream"],
            version=data["version"],
            context=data["context"],
            arch=data["arch"],
        )
