.. _source_koji:

Source: koji
============

The ``koji`` push source allows the loading of content from an instance of
`koji <https://pagure.io/koji/>`_.

Supported content types:

* RPMs
* container images (with operator manifests if applicable)
* modulemd YAML streams (yum repo metadata)
* virtual machine images

Note that many features of the koji source requires having koji's volume(s) mounted
locally.


koji source URLs
----------------

The base form of a Koji source URL is:

``koji:koji-xmlrpc-endpoint?contenttype1=...[&contenttype2=...[&...]]``

For example, accessing a couple of RPMs from Fedora koji may be achieved by
URL:

``koji:https://koji.fedoraproject.org/kojihub?rpm=python3-3.7.5-2.fc31.x86_64.rpm,python3-3.7.5-2.fc31.src.rpm``

The next subsections provide more detail on specific content types.


Accessing RPMs
..............

Use the ``rpm`` parameter to request RPMs by filename.

``koji:https://koji.fedoraproject.org/kojihub?rpm=python3-3.7.5-2.fc31.x86_64.rpm``

This will yield unsigned RPMs by default.  If you require signed RPMs,
specify the signing key(s) in the ``signing_key`` parameter. You must use
the same short key IDs as used on the koji instance, and a fatal error will
occur if signed RPMs are not available.

``koji:https://koji.fedoraproject.org/kojihub?rpm=python3-3.7.5-2.fc31.x86_64.rpm&signing_key=12c944d0``


Accessing modulemd streams
..........................

Use the ``module_build`` parameter to request modulemd streams from one or more
builds.  Builds can be specified by NVR.  Use the NVR of build(s) containing modulemd
text files as archives (shown as "Module Archives" in the Koji UI).

``koji:https://koji.fedoraproject.org/kojihub?module_build=flatpak-common-f32-3220200518173809.caf21102``

If you want to process only a subset of the modules on the build
(i.e. select only certain arches), you may use ``module_filter_filename`` to select
the desired modulemd files, as in example:

``koji:https://koji.fedoraproject.org/kojihub?module_build=flatpak-common-f32-3220200518173809.caf21102&module_filter_filename=modulemd.x86_64.txt,modulemd.s390x.txt``

Accessing container images
..........................

Use the ``container_build`` parameter to request container images from one or
more builds. Builds can be specified by NVR. Builds should be produced by
`OSBS`_ or should use compatible metadata.

``koji:https://koji.fedoraproject.org/kojihub?container_build=grafana-7-1``

Push items produced in this case may include:

- :class:`~pushsource.ContainerImagePushItem` - one for each available image
- :class:`~pushsource.SourceContainerImagePushItem` - for source container images
- :class:`~pushsource.OperatorManifestPushItem` - if images have attached operator
  manifest archives

Accessing virtual machine images
...............................

Use the ``vmi_build`` parameter to request virtual machine images from one or
more builds. Builds can be specified by NVR. Builds should be produced by
`Image Builder`_ or should use compatible metadata.

``koji:https://koji.fedoraproject.org/kojihub?vmi_build=fedora-azure-37-1.7``

Push items produced in this case may include:

- :class:`~pushsource.VMIPushItem` - one for each available image
- :class:`~pushsource.VHDPushItem` - for Azure VHD images.
- :class:`~pushsource.AmiPushItem` - for AMI raw images.

Setting the destination for push items
......................................

As koji itself contains no policy regarding where content should be pushed,
a koji source by default yields all push items with an empty destination.

If you know ahead of time the destination(s) to which your push items should be distributed,
you may include these in the ``dest`` parameter, as in example:

``koji:https://koji.fedoraproject.org/kojihub?module_build=flatpak-common-f32-3220200518173809.caf21102&dest=target-repo1,target-repo2``


Adjusting ``koji.BASEDIR``
..........................

Some features of the koji source require read-only access to koji's working volume(s).
The top-level path by default is provided by the ``koji`` library as ``/mnt/koji``.

To use a different path, include ``basedir`` in the source URL:

``koji:https://koji.fedoraproject.org/kojihub?module_build=flatpak-common-f32-3220200518173809.caf21102&basedir=/mnt/my-local-koji``



Python API reference
--------------------

.. autoclass:: pushsource.KojiSource
   :members:
   :special-members: __init__


.. _OSBS: https://osbs.readthedocs.io/
.. _Image Builder: https://www.osbuild.org/guides/image-builder-service/image-builder-koji.html
