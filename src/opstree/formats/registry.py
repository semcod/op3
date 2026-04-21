"""Format registry — wrapper around fraq's FormatRegistry."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from fraq.formats import FormatRegistry as FraqFormatRegistry


class FormatRegistry:
    """Registry for format adapters (wraps fraq's FormatRegistry)."""
    
    _registry = FraqFormatRegistry()
    
    @classmethod
    def register(cls, name: str, adapter: Optional[Callable] = None):
        """Register a format adapter. Can be used as a decorator."""
        return cls._registry.register(name, adapter)
    
    @classmethod
    def get(cls, name: str) -> Callable:
        """Get a format adapter by name."""
        return cls._registry.get(name)
    
    @classmethod
    def available(cls) -> List[str]:
        """Get list of available format names."""
        return cls._registry.available()
    
    @classmethod
    def serialize(cls, name: str, data: Any, **kwargs) -> Any:
        """Serialize data using the specified format."""
        return cls._registry.serialize(name, data, **kwargs)


def register_format(name: str, adapter: Optional[Callable] = None):
    """Decorator to register a format adapter."""
    return FormatRegistry.register(name, adapter)
