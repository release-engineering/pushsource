.. _userguide:

User Guide
==========

The pushsource library provides a common interface over various sources
of content, yielding metadata on each piece of content found.
These pieces of metadata are referred to as "push items", as the main use-case
for the library is in the creation of content publishing tools.

Here are some examples of push items:

- RPMs obtained from a `koji <https://pagure.io/koji/>`_ server.
- RPMs and generic files obtained from a local directory.
- Advisories and RPMs obtained from Errata Tool.

Typical usage of the library involves obtaining a :class:`~pushsource.Source`
instance and iterating over :class:`~pushsource.PushItem` objects discovered
by the source.

.. contents::

.. _urls:

Obtaining a source by URL
-------------------------

In most cases, the recommended method of obtaining a :class:`~pushsource.Source`
is to provide a URL to the :meth:`~pushsource.Source.get` method.
URLs are used to select a backend and provide parameters.

URLs use one of the following syntaxes:

::

  backend:remote_url?arg1=val1&arg2=val2&...
  backend:arg1=val1&arg2=val2&...
  backend:

The first syntax with a `remote_url` may be used in the common case where the
desired backend itself needs the URL of a remote service in order to function.

The second syntax omits the `remote_url` in cases where the backend does not
accept a URL.

The final syntax is used in cases where the backend does not require any arguments
in order to function.

When using URLs to obtain a source, arguments may consist of only strings and lists
of strings. By convention, most backends accept lists both by repeating the argument
name multiple times, and also by comma-separated values.

::

  backend:list_arg=val1&list_arg=val2
  # Is equivalent to:
  backend:list_arg=val1,val2

Here are some example URLs:

::

  # Load some RPMs from the Fedora Project's koji
  koji:https://koji.fedoraproject.org/kojihub?rpm=python3-3.7.5-2.fc31.x86_64.rpm,python3-3.7.5-2.fc31.src.rpm

  # Load an advisory from Errata Tool
  errata:https://errata.example.com/?errata=RHBA-2020:1234

  # A hypothetical backend which accepts no arguments
  mock:


Available backends
------------------

The pushsource library includes the following backends.
For detailed information, see the API reference of the associated class.

+----------+-----------------------------------------------------------------------------+-------------------------------------+----------------------------------------------------+
| Name     | Examples                                                                    | Class                               | Description                                        |
+==========+=============================================================================+=====================================+====================================================+
| koji     | ``koji:https://koji.fedoraproject.org?rpm=python3-3.7.5-2.fc31.x86_64.rpm`` | :class:`~pushsource.KojiSource`     | Obtain RPMs, container images and other content    |
|          |                                                                             |                                     | from a koji server                                 |
+----------+-----------------------------------------------------------------------------+-------------------------------------+----------------------------------------------------+
| staged   | ``staged:/mnt/vol/my/staged/content``                                       | :class:`~pushsource.StagedSource`   | Obtain RPMs, files, AMIs and other content from    |
|          |                                                                             |                                     | locally mounted filesystem                         |
+----------+-----------------------------------------------------------------------------+-------------------------------------+----------------------------------------------------+
| registry | ``registry:registry.access.redhat.com/ubi8/ubi:latest``                     | :class:`~pushsource.RegistrySource` | Obtain images from a container image registry      |
|          |                                                                             |                                     |                                                    |
+----------+-----------------------------------------------------------------------------+-------------------------------------+----------------------------------------------------+
| errata   | ``errata:https://errata.example.com?errata=RHBA-2020:1234``                 | :class:`~pushsource.ErrataSource`   | Obtain RPMs, container images and advisory         |
|          |                                                                             |                                     | metadata from Errata Tool                          |
+----------+-----------------------------------------------------------------------------+-------------------------------------+----------------------------------------------------+


Processing push items
---------------------

Once a ``Source`` instance has been obtained, it can be iterated over to obtain
instances of :class:`~pushsource.PushItem`.

Each object yielded by the source may be an instance of any ``PushItem`` subclass,
depending on the type of content loaded by the source.  For example, RPMs will be
yielded as instances of :class:`~pushsource.RpmPushItem` and errata will be yielded
as instances of :class:`~pushsource.ErratumPushItem`.

Commonly, different kinds of processing will be needed for different kinds of push items.
In this case, it's recommended to use :func:`isinstance` checks to dispatch each push
item appropriately.

Consider tolerating push items of an unknown type (perhaps with a warning). This will ensure
your code is forwards-compatible with later versions of this library, which may add new types
of push items to existing sources.

Example:

::

  with Source.get(...) as source:
    for item in source:
      if isinstance(item, RpmPushItem):
        publish_rpm(item)
      elif isinstance(item, ErratumPushItem):
        publish_erratum(item)
      elif isinstance(item, FilePushItem):
        publish_file(item)
      else:
        LOG.warning("Unexpected push item type: %s", item)


.. _implementing:

Implementing a backend
----------------------

New backends can be registered with the library, making them accessible via URL.
To implement a backend, follow these steps:

* Create a class inheriting from :class:`~pushsource.Source`.
* In your constructor, add any arguments you'd like to be usable in URLs for your backend,
  while following these conventions:
    * Remember that all arguments from URLs will be provided as strings.
    * Accept a `url` argument if and only if you want your backend URL to accept a URL
      immediately after the backend scheme (as in example ``backend:url?arg=val&arg=val&...``).
    * If your backend uses a customizable number of threads, use an argument named `threads`
      for configuring the number of threads.
    * If your backend has a customizable timeout, use an argument named `timeout` accepting
      a number of seconds.
* Implement the ``__iter__`` method, while following conventions:
    * Lazy loading of data is recommended where practical; i.e. prefer to implement a generator
      which yields each piece of data as it is ready, rather than eagerly loading all data
      into a list.
* If your class allocates any resources which should be cleaned up when no longer needed,
  implement ``__enter__`` and ``__exit__`` methods to manage them.
* Call the :class:`~pushsource.Source.register_backend` method providing your backend's name
  and class as arguments.

After following the above steps, instances of your source can be obtained by
:meth:`~pushsource.Source.get`, in the same manner as backends built-in to the library.


.. _binding:

Binding partially-configured backends
-------------------------------------

For developers integrating this library into an environment where certain parameters
are known ahead of time, it's possible and recommended to preconfigure backends,
making them less cumbersome to use and hiding configuration details. This can be done
by registering a new backend which acts as an alias along with a set of arguments
to an existing backend.

For example: this library ships a `koji` backend. If we are developing a tool which
frequently is used with Fedora Koji, it would be cumbersome to require the user to
pass the Fedora Koji URL every time the source is used. This can be fixed by
creating a `fedkoji` alias, which delegates to the `koji` backend with some arguments
pre-filled.

::

  # make a 'fedkoji' backend which is simply the koji backend
  # pointed at a particular URL
  fedkoji_backend = Source.get_partial('koji:https://koji.fedoraproject.org/kojihub')
  Source.register_backend('fedkoji', fedkoji_backend)

  # fedora koji now accessible without specifying URL
  Source.get('fedkoji:rpm=python3-3.7.5-2.fc31.x86_64.rpm,...')

