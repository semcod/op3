"""Format adapters for reading/writing different configuration formats."""
from opstree.formats.registry import FormatRegistry, register_format

__all__ = [
    "FormatRegistry", "register_format",
]
