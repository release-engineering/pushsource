# Helpers for py2 vs py3 compatibility issues.

try:
    from os import scandir
except ImportError:  # pragma: no cover
    # expected path for python <3.5
    from scandir import scandir

__all__ = ["scandir"]
