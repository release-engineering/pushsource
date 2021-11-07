pushsource
==========

A library for accessing push items from various sources.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   userguide
   sources/base
   sources/staged
   sources/koji
   sources/registry
   sources/errata
   model/base
   model/files
   model/rpm
   model/modulemd
   model/errata
   model/containers
   model/ami
   model/productid
   model/comps
   schema/staged
   schema/errata

Quick Start
-----------

Install pushsource from PyPI:

::

    pip install pushsource

In your python code, obtain a :class:`~pushsource.Source` instance,
iterate over the source to obtain push items, and perform desired operations
according to their type and attributes:

.. code-block:: python

    from pushsource import Source, RpmPushItem
    import logging

    with Source.get('koji:https://koji.fedoraproject.org/kojihub?rpm=rpm1,rpm2,...') as source:
        for item in source:
            if isinstance(item, RpmPushItem):
                # do something with RPMs
                publish_rpm(item)
            else:
                # don't know what to do
                logging.getLogger().warning("Unexpected item: %s", item)

For more information, see the :ref:`userguide`.
