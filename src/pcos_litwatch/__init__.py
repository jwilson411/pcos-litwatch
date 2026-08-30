"""PCOS literature collector. Stdlib only. No secrets."""

__version__ = "0.1.0"

from .collect import collect
from .record import Record

__all__ = ["collect", "Record", "__version__"]
