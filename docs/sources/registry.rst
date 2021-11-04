Source: registry
================

The ``registry`` push source allows the loading of content from a
`container image registry <https://docs.docker.com/registry/spec/api/>`_.

Supported content types:

* Container images
* Source container images


registry source URLs
--------------------

The base form of a Registry source URL is:

``registry:image=pullspec1[,pullspec2[,...]]``

..where each ``pullspec`` is of the form used by tools such as ``docker pull``,
with the following restrictions:

- the pullspec must reference an image by tag (not digest)
- the pullspec must always include the registry hostname

For example, the following URL accesses a single image by tag:

``registry:image=registry.access.redhat.com/ubi8/ubi:8.4-211``


Authentication
--------------

If the registry host requires authentication, credentials for the registry
must be available from ``$HOME/.docker/config.json`` using the same format
as consumed by ``docker`` and ``podman``.


Python API reference
--------------------

.. autoclass:: pushsource.RegistrySource
   :members:
   :special-members: __init__
