Source: konflux
================

The ``konflux`` push source allows the loading of content from local JSON files
organized by advisory. This source is designed for use with Konflux-generated
advisory metadata and queries a Pulp 3 server to resolve RPM content hrefs.

Supported content types:

* RPMs
* Advisories

The source is designed to be extensible and can support additional content types
(such as modules, container images, etc.) in the future as needed.

konflux source URLs
-------------------

The base form of a konflux source URL is:

``konflux:base-directory?advisories=RHXA-XXXX:0001[,RHXA-XXXX:0002[,...]]``

For example, referencing a single advisory would look like:

``konflux:/path/to/konflux/data?advisories=RHSA-2020:0509``

Multiple advisories can be specified with a comma-separated list:

``konflux:/path/to/konflux/data?advisories=RHSA-2020:0509,RHSA-2020:0510``

Pulp 3 connection parameters (``pulp_url``, ``pulp_cert``, ``pulp_key``,
``pulp_domain``) are required and can be provided as URL query parameters,
keyword arguments to :meth:`~pushsource.Source.get`, or environment variables
(see :class:`~pushsource.KonfluxSource` for details).

The base directory should contain subdirectories named after each advisory ID.
Each advisory subdirectory must contain:

* ``advisory_cdn_metadata.json`` - Advisory metadata (title, severity, references, packages, etc.)
* ``advisory_cdn_filelist.json`` - RPM file list with checksums, signing keys, and repository destinations

Directory structure
...................

Example directory structure::

    /path/to/konflux/data/
    ├── RHSA-2020:0509/
    │   ├── advisory_cdn_metadata.json
    │   └── advisory_cdn_filelist.json
    └── RHSA-2020:0510/
        ├── advisory_cdn_metadata.json
        └── advisory_cdn_filelist.json

File format
...........

**advisory_cdn_metadata.json**

This file contains advisory metadata in the standard Errata Tool format, including:

* Advisory ID, title, description, severity
* Package list with checksums
* References (CVEs, Bugzilla links, etc.)
* Release information

**advisory_cdn_filelist.json**

This file contains build and RPM information::

    {
      "build-nvr": {
        "rpms": {
          "rpm-filename.rpm": ["repo1", "repo2", ...]
        },
        "checksums": {
          "md5": {
            "rpm-filename.rpm": "checksum-value"
          },
          "sha256": {
            "rpm-filename.rpm": "checksum-value"
          }
        },
        "sig_key": "signing-key-id"
      }
    }

Differences from `ErrataSource`
...............................

Unlike the `ErrataSource`, the `KonfluxSource`:

* Reads from local JSON files rather than querying the Errata API
* Does not require Koji integration
* Queries Pulp 3 by SHA256 to resolve RPM ``pulp_href`` for Pulp-to-Pulp syncing
* Does not currently support filtering by architecture (this use case may be supported in the future)
* Currently produces RPMs and advisories (additional content types such as modules and container images can be supported in the future)

Python API reference
--------------------

.. autoclass:: pushsource.KonfluxSource
   :members:
   :special-members: __init__
