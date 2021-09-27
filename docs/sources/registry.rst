Source: registry
==============

The ``registry`` push source allows push container content from external docker
registry

Supported content types:

* Container images


registry URLs
------------------

Registry source can be obtained by specifying URL:

``registry:registry-hostname/namespace/repository:tag``

For example, referencing a single advisory would look like:

``registry.access.redhat.com/ubi8/ubi:8.4-211``


Populating registry container push items
........................................

Each push item is specified by one entry in uris list accepted by source.
Every URI is inspected as container image which serves as identification
for source containers. Manifest is also fetched from the specified URL
to determine which manifest type is served by registry. Registry source
class requests for manifest list, but anything v2 valid returned by registry
is accepted

Python API reference
--------------------

.. autoclass:: pushsource.RegistrySource
   :members:
   :special-members: __init__
