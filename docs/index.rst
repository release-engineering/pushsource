pushsource
==========

A library for accessing push items from various sources.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   userguide
   sources/staged
   sources/koji
   sources/errata
   model/base
   model/files
   model/rpm
   model/modulemd
   model/errata
   model/ami
   model/productid
   model/comps
   model/channeldumps
   schema/staged
   schema/errata

Quick Start
-----------

Install pushsource from PyPI:

::

    pip install pushsource

In your python code, obtain a :class:`~pushsource.Source` instance and
iterate over the returned push items:

.. code-block:: python

    from pushsource import Source

    source = Source.get('koji:https://koji.fedoraproject.org/kojihub?rpm=rpm1,rpm2,...')

    for item in source:
        process(item)

Sources are typically obtained by URL.
