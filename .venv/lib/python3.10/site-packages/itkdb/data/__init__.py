from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources
path = resources.files("itkdb") / "data"

__all__ = [
    "path",
]
