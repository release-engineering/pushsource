import sys

import attr

# Wrappers for attr module to deal with some incompatibilities between versions


def s():
    kwargs = {"frozen": True, "slots": True}
    if sys.version_info >= (3,):
        kwargs["kw_only"] = True
    return attr.s(**kwargs)


ib = attr.ib
evolve = attr.evolve
validators = attr.validators
Factory = attr.Factory
