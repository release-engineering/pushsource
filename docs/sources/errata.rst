Source: errata
==============

The ``errata`` push source allows the loading of content from an instance of
Errata Tool (or "ET").

Supported content types:

* RPMs
* Container images
* Advisories
* Virtual machine images


errata source URLs
------------------

The base form of an errata source URL is:

``errata:errata-tool-url?errata=RHXA-XXXX:0001[,RHXA-XXXX:0002[,...]]``

For example, referencing a single advisory would look like:

``errata:https://errata.example.com?errata=RHBA-2020:1234``

The provided Errata Tool URL should be the base URL of the service,
and not any specific API endpoint.


Setting the koji source
.......................

In order to obtain metadata about RPMs, the errata source
needs to be configured to point at the same koji environment as used by
the connected ET environment.  This can be done by providing a partial URL
for a koji source in the ``koji_source`` parameter (leave parameters for selecting
content, such as ``rpm``, blank - the errata source will fill them in as needed).

For example, if our ET environment is connected to Fedora Koji, we could configure
this as:

``errata:https://errata.example.com?errata=RHBA-2020:1234&koji_source=koji:https://koji.fedoraproject.org/kojihub``

Although it is technically possible to configure the koji source behavior using
any of the parameters documented in :ref:`source_koji`, in practice this results
in unwieldy URLs with multiple levels of URL encoding.  Thus it's recommended
that developers integrating this library with their services should preconfigure
commonly used koji sources, so that they can be referred to by a short identifier.

For example, if the ``fedkoji`` source has been configured as explained in :ref:`binding`,
the source can be referred to more succintly as in:

``errata:https://errata.example.com?errata=RHBA-2020:1234&koji_source=fedkoji``


Python API reference
--------------------

.. autoclass:: pushsource.ErrataSource
   :members:
   :special-members: __init__
