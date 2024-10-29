Source: staged
==============

The ``staged`` push source allows the loading of content from any locally accessible
directory referred to as the staging area. Content types and destinations are defined
by the directory structure in the staging area, and additional metadata for content
can be provided in a YAML or JSON file.

Supported content types:

* RPMs
* Advisories
* Generic files
* Content Gateway metadata
* Complete directories
* Amazon Machine Images (AMIs)
* comps.xml files (yum repo metadata)
* modulemd YAML streams (yum repo metadata)
* productid files (yum repo metadata)


Staged source URLs
------------------

A `staged` source is obtained by URL:

``staged:stagedir1[,stagedir2[,stagedir3[,...]]]``

One or more staging directories must be provided (usually, exactly one).
Each staging directory must use the :ref:`staging_structure` defined below.

Here are some examples of `staged` source URLs:

* ``staged:/mnt/volume/my-staging-area`` - a single staging directory
* ``staged:/mnt/shared/stage1,/mnt/shared/stage2`` - two staging directories


.. _staging_structure:

Staging structure
-----------------

Here is a brief overview of the structure of a staging directory:

::

  root/
  root/staged.yaml  # optional
  root/destination/
  root/destination/COMPS/*.xml
  root/destination/ERRATA/*
  root/destination/FILES/*
  root/destination/CGW/*
  root/destination/PRODUCTID/*
  root/destination/MODULEMD/*
  root/destination/RPMS/*.rpm
  root/destination/AWS_IMAGES/*
  root/destination/CLOUD_IMAGES/*
  root/destination/RAW/*

The staging directory consists of:

- an optional file including some metadata for files in the staging area
- a directory for each "destination" of content in this staging area
- subdirectories for each type of content
- files containing the content to be pushed or manipulated

These are explained in further detail below.


root/staged.yaml
................

This file provides additional metadata on the content in the staging area.

It is generally mandatory for file types which do not embed their own metadata
(such as ``FILES`` and ``AWS_IMAGES``), and is unused for file types such as
``RPMS`` which have all necessary metadata built-in to the file format.

Here's an example to give an idea of the metadata controlled by this file:

::

   header:
      version: "0.2" # current schema version - don't change

   payload:
      files:
         # desired name, doesn't need to be same as staged filename
       - filename: "RHEL-6.7-20150429.0-Client-i386-boot.iso"

         # path relative to staging directory
         relative_path: "rhel-6-desktop-beta-isos__6Client__i386/FILES/RHEL-6.7-20150429.0-Client-i386-boot.iso"

         # SHA256 checksum
         sha256sum: b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b878ae4944c

         # Additional attributes
         attributes:
            # human-readable description
            description: "Red Hat Enterprise Linux 6.7 Boot DVD"

:ref:`staging_schema` provides a complete reference of the fields which can be set by this
file.

For historical reasons, the file may also be provided as JSON and named
``pub-mapfile.json``.


root/destination/
.................

A directory exists for each discrete destination of content in this staging area.

The meaning of ``destination`` depends on the context in which the staging area is
used.  For example, if this staging area is being used to publish content into a Pulp
server, each ``destination`` will be a Pulp repository name.  This library does not
enforce any semantics on these destination names.

Note that, if a single piece of content should be published to multiple destinations,
the content needs to be placed in multiple ``destination`` directories. Symlinks
are often used for this to avoid duplication.


root/destination/COMPS/\*.xml
.............................

Each file in ``COMPS`` should be a comps XML file in the yum repo metadata format,
defining package groups.

Will yield instances of :class:`~pushsource.CompsXmlPushItem`.

root/destination/ERRATA/\*
..........................

Each file in ``ERRATA`` should be a YAML or JSON dump containing advisory metadata.

The format is essentially the same as that produced by Errata Tool's XML-RPC APIs.
:ref:`errata_schema` formally documents the schema.

Will yield instances of :class:`~pushsource.ErratumPushItem`.

root/destination/FILES/\*
.........................

Each file in ``FILES`` can be any type of file, to be published verbatim.
In practice, this is often used for binary files such as ISO disc images or
installers.

Files in this directory must have metadata included in ``staged.yaml``.

For historical reasons, this directory may also be named ``ISOS``.

Will yield instances of :class:`~pushsource.FilePushItem`.

root/destination/CGW/\*
.........................

Each file in CGW should be a valid YAML containing a list of definitions for objects in Content Gateway.

Will yield instances of :class:`~pushsource.CGWPushItem`.

root/destination/PRODUCTID/\*
.............................

Each file in ``PRODUCTID`` should be a PEM-formatted product certificate,
as used by Satellite 6 / RHSM.

Will yield instances of :class:`~pushsource.ProductIdPushItem`.

root/destination/MODULEMD/\*
............................

Each file in ``MODULEMD`` should be a valid YAML stream containing modulemd
and/or modulemd-defaults documents.

Will yield instances of :class:`~pushsource.ModuleMdPushItem`.

root/destination/RPMS/\*.rpm
............................

Each file in ``RPMS`` should be an RPM. Various metadata will be parsed from
RPM headers.

For historical reasons, this directory may also be named ``SRPMS``. It is not
required that source RPMs are placed in the ``SRPMS`` directory.

Will yield instances of :class:`~pushsource.RpmPushItem`.

root/destination/AWS_IMAGES/\*
..............................

Each file in ``AWS_IMAGES`` should be an EBS snapshot for use as an
Amazon Machine Image (AMI).

Files in this directory must have metadata included in ``staged.yaml``.

Will yield instances of :class:`~pushsource.AmiPushItem`.

root/destination/CLOUD_IMAGES/\*
................................

Each directory within ``CLOUD_IMAGES`` should contain one or more VMI(s) plus a
``resources.yaml`` .

The ``resources.yaml`` contains all the information needed for the
images in that folder.

:ref:`cloud_schema` provides a complete reference of the fields which can be set by this
file.

Will yield instances of either :class:`~pushsource.AmiPushItem` or
:class:`~pushsource.VHDPushItem`.

root/destination/RAW/\*
.......................

``RAW`` should generally be interpreted as a request to recursively publish the
entire directory tree as-is. Each file in ``RAW`` can be any type of file, to be
published verbatim. In practice, ``RAW`` is used for kickstart trees, ostrees, and
origin-only content.

Will yield instances of :class:`~pushsource.DirectoryPushItem`.



Python API reference
--------------------

.. autoclass:: pushsource.StagedSource
   :members:
   :special-members: __init__
