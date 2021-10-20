Source: registry
==============

The ``registry`` push source allows push container content from external docker
registry

Supported content types:

* Container images


registry URLs
------------------

Registry source can be obtained by specifying URL + dest tags:

``registry-hostname/namespace/repository:tag:dest-tag1:dest-tag2``

For example, referencing a single advisory would look like:

``registry.access.redhat.com/ubi8/ubi:8.4-211:latest``

To get source with push items populated from external registry you call 
Source.get like this:

.. code:
   Source.get("registry:images_str=registry.access.redhat.com/ubi8/ubi:8.4-211:latest,registry.access.redhat.com/ubi8/ubi:8.3:8.3&dest=ubi-fork&signing_key=01abcdef01234567")

Code above will produce two push items:
- dest=ubi-fork:latest
  src=registry.access.redhat.com/ubi8/ubi:8.4-211
  signing_key=01abcdef01234567

- dest=ubi-fork:8.3
  src=registry.access.redhat.com/ubi8/ubi:8.3
  signing_key=01abcdef01234567

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
