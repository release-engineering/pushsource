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
* Channel dump ISOs (for RHN Classic)
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

(to be documented!)


Python API reference
--------------------

.. autoclass:: pushsource.StagedSource
   :members:
