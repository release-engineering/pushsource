pushsource
==========

A library for accessing push items from various sources.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   userguide
   api/sources
   api/pushitems

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
