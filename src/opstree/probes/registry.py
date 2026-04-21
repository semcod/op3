"""Probe registry for dynamic probe registration."""
from __future__ import annotations
from typing import Dict, List, Type, Callable, Optional
from opstree.probes.base import Probe


class ProbeRegistry:
    """Registry for probes by layer_id."""
    
    _probes: Dict[str, List[Probe]] = {}
    
    @classmethod
    def register(cls, probe: Probe) -> None:
        """Register a probe for its layer_id."""
        if probe.layer_id not in cls._probes:
            cls._probes[probe.layer_id] = []
        cls._probes[probe.layer_id].append(probe)
    
    @classmethod
    def get(cls, layer_id: str) -> List[Probe]:
        """Get all probes for a given layer_id."""
        return cls._probes.get(layer_id, [])
    
    @classmethod
    def all(cls) -> Dict[str, List[Probe]]:
        """Get all registered probes."""
        return cls._probes.copy()


def register_probe(probe_class: Type[Probe]) -> Type[Probe]:
    """Decorator to register a probe class."""
    # Note: This is a simple decorator that assumes the class will be instantiated
    # In practice, you might want to register instances or use a different pattern
    def wrapper(*args, **kwargs):
        instance = probe_class(*args, **kwargs)
        ProbeRegistry.register(instance)
        return instance
    return wrapper
