import attr

# importlib.metadata is available for py3.8 and higher
# previous versions get it from importlib_metadata installed
# from importlib-metadata
try:
    from importlib.metadata import version
except ImportError:  # pragma: no cover
    from importlib_metadata import version


# Wrappers for attr module to deal with some incompatibilities between versions


ATTR_VERSION = tuple(int(x) for x in (version("attrs")).split(".")[0:2])


def s():
    kwargs = {"frozen": True, "slots": True}
    if ATTR_VERSION >= (18, 2):
        kwargs["kw_only"] = True
    return attr.s(**kwargs)


ib = attr.ib
evolve = attr.evolve
validators = attr.validators
Factory = attr.Factory
