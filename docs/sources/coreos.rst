Source: coreos
==============

The ``coreos`` push source allows the loading of content from a JSON file of OpenShift CoreOS installer from GitHub.

Supported content types:

* AMIs
* VHDs


coreos source URLs
------------------

The base form of an coreos source URL is:

``coreos:github-url?paths=path1[,path2[,...]]``

For example, retrieving the JSON files for the RHEL 9 and RHEL 10 CoreOS installer would look like:

``coreos:https://github.com/openshift/installer/tree/master?paths=data/coreos-rhel-9.json,data/coreos-rhel-10.json``

The provided GitHub URL should be the base URL of the repository,
and should contain the tag or branch name of the repository.

Python API reference
--------------------

.. autoclass:: pushsource.CoreOSSource
   :members:
   :special-members: __init__
