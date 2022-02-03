import logging

from ...validator import Validator
from ... import compat_attr as attr

REQUIRED_VERSION = "0.2"
VALIDATOR = Validator("staged", ids=["relative_path"])
LOG = logging.getLogger("pushsource")


@attr.s()
class StagingFileMetadata(object):
    attributes = attr.ib(type=dict)
    filename = attr.ib(type=str)
    relative_path = attr.ib(type=str)
    sha256sum = attr.ib(type=str)
    version = attr.ib(type=str)
    order = attr.ib(type=float)


@attr.s()
class StagingMetadata(object):
    # A private class modelling the content of staging metadata files

    # Filename from which metadata was loaded.
    filename = attr.ib(type=str, default=None)

    # Metadata per file, keyed by relative path within staging area
    file_metadata = attr.ib(type=dict, default=attr.Factory(dict))

    def file_metadata_or_die(self, relative_path):
        # Return StagingFileMetadata corresponding to relative_path, or raise a fatal error
        # if not available.
        file_md = self.file_metadata.get(relative_path)
        if file_md is None:
            message = "No metadata available for %s" % relative_path
            if self.filename:
                message = "%s in %s" % (message, self.filename)
            raise ValueError(message)

        return file_md

    @classmethod
    def from_data(cls, data, filename="<unknown file>"):
        VALIDATOR.validate(data, filename)

        payload = data.get("payload") or {}
        files = payload.get("files") or []
        file_metadata = {}

        for entry in files:
            md = StagingFileMetadata(
                attributes=entry.get("attributes") or {},
                filename=entry.get("filename"),
                relative_path=entry["relative_path"],
                sha256sum=entry.get("sha256sum"),
                version=entry.get("version"),
                order=entry.get("order"),
            )
            if md.relative_path in file_metadata:
                raise ValueError(
                    "File %s listed twice in %s" % (md.relative_path, filename)
                )
            file_metadata[md.relative_path] = md

        return cls(filename=filename, file_metadata=file_metadata)


@attr.s()
class StagingLeafDir(object):
    # A private class modelling a leaf directory within a staging area.
    file_type = attr.ib(type=str)
    dest = attr.ib(type=str)
    path = attr.ib(type=str)
    topdir = attr.ib(type=str)
