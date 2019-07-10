from ... import compat_attr as attr

REQUIRED_VERSION = "0.2"


@attr.s()
class StagingFileMetadata(object):
    # A private class modelling a single entry in staging metadata
    # {
    #     "attributes": {
    #         "description": "Red Hat Ceph 4.0 Binary DVD for RHEL 8 Hosts"
    #     },
    #     "filename": "rhceph-4.0-rhel-8-x86_64.iso",
    #     "relative_path": "rhceph-4-for-rhel-8-x86_64-files/ISOS/rhceph-4.0-rhel-8-x86_64.iso",
    #     "sha256sum": "197cb195354dc55d78323e6d095c84e324f52e08bbd4f69d0514ca8c2f90a2bf",
    #     "version": "4.0"
    # },

    attributes = attr.ib(type=dict)
    filename = attr.ib(type=str)
    relative_path = attr.ib(type=str)
    sha256sum = attr.ib(type=str)
    # Not sure what this is??
    # version = attr.ib(type=str)


@attr.s()
class StagingMetadata(object):
    # A private class modelling the content of staging metadata files

    # Filename from which metadata was loaded.
    filename = attr.ib(type=str)

    # Metadata per file, keyed by relative path within staging area
    file_metadata = attr.ib(type=dict)

    @classmethod
    def from_data(cls, data, filename="<unknown file>"):
        header = data.get("header") or {}
        version = header.get("version")

        # TODO: make a jsonschema and then validate it here.

        # Currently the only supported version...
        if version != REQUIRED_VERSION:
            raise ValueError(
                "%s has unsupported version (has: %s, required: %s)"
                % (filename, version, REQUIRED_VERSION)
            )

        payload = data.get("payload") or {}
        files = payload.get("files") or []
        file_metadata = {}

        for entry in files:
            md = StagingFileMetadata(
                attributes=entry.get("attributes") or {},
                filename=entry["filename"],
                relative_path=entry["relative_path"],
                sha256sum=entry["sha256sum"],
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
