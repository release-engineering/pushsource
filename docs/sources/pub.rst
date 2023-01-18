Source: pub
==============

The ``pub`` push source allows the loading of content from an instance of Pub.

Supported content types:

* AMIs


pub source URLs
------------------

The base form of an pub source URL is:

``pub:pub-url?task_id=100[,200[,...]]``

For example, referencing a single task would look like:

``pub:https://pub.example.com?task_id=1234``

The provided Pub URL should be the base URL of the service,
and not any specific API endpoint.

Python API reference
--------------------

.. autoclass:: pushsource.PubSource
   :members:
   :special-members: __init__
