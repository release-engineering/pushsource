Push items
==========

All push items provided by this library inherit from a common class
documented here.

Every push item class has the following properties:

* push item classes use `attrs <http://www.attrs.org/en/stable/>`_.
* instances are immutable; use helper functions such as :func:`attr.evolve`
  to obtain a modified push item.

.. autoclass:: pushsource.PushItem()
   :members:

.. autoclass:: pushsource.KojiBuildInfo()
   :members:
