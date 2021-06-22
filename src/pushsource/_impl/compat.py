# Helpers for py2 vs py3 compatibility issues.

import sys

try:
    from os import scandir
except ImportError:  # pragma: no cover
    # expected path for python <3.5
    from scandir import scandir

if sys.version_info >= (3, 0):
    # It is preferred to use immutable dicts when possible
    from frozendict import frozendict
else:  # pragma: no cover
    # But it's not available on py2, fall back to plain old dicts there
    frozendict = dict


__all__ = ["scandir", "frozendict"]
