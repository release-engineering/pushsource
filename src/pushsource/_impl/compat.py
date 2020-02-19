# Helpers for py2 vs py3 compatibility issues.

try:
    from os import scandir
except ImportError:  # pragma: no cover
    # TODO: is scandir able to work on python 2.6?
    from scandir import scandir

__all__ = ["scandir"]
