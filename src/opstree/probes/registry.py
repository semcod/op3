"""Probe registry for dynamic probe registration.

Historical note
---------------

Prior to 0.1.8 this module defined ``register`` / ``get`` / ``all`` as
``@classmethod``, which meant every :class:`ProbeRegistry` instance
actually shared the same class-level ``_probes`` dict. That made it
impossible to scope probes per scanner — assigning a custom registry to
``scanner.probe_registry`` silently fell through to the global state,
and concurrent / repeated scans accumulated probes unpredictably.

0.1.8 makes the methods proper instance methods. The module-level
``_default_registry`` keeps the :func:`register_probe` decorator's
implicit "register on import" semantics working for existing users.
"""
from __future__ import annotations
from typing import Dict, List, Type, Callable, Optional
from opstree.probes.base import Probe


class ProbeRegistry:
    """Registry for probes keyed by ``layer_id``.

    Each instance owns its own probe dict — create a fresh registry per
    scanner if you want isolation from the process-global default.
    """

    def __init__(self) -> None:
        self._probes: Dict[str, List[Probe]] = {}

    def register(self, probe: Probe) -> None:
        """Register a probe for its ``layer_id``."""
        self._probes.setdefault(probe.layer_id, []).append(probe)

    def get(self, layer_id: str) -> List[Probe]:
        """Return all probes registered for ``layer_id``."""
        return list(self._probes.get(layer_id, []))

    def all(self) -> Dict[str, List[Probe]]:
        """Return a shallow copy of the full probe map."""
        return {lid: list(probes) for lid, probes in self._probes.items()}

    def clear(self) -> None:
        """Remove all probes — primarily useful in tests."""
        self._probes.clear()


# Process-global registry used by the :func:`register_probe` decorator.
# Application code should prefer creating a dedicated registry per scanner.
_default_registry: ProbeRegistry = ProbeRegistry()


def get_default_registry() -> ProbeRegistry:
    """Return the process-global default registry.

    Exposed so legacy callers that relied on ``ProbeRegistry.register(p)``
    / ``ProbeRegistry.get(id)`` have a clear migration target.
    """
    return _default_registry


def register_probe(probe_class: Type[Probe]) -> Callable[..., Probe]:
    """Decorator: instantiate ``probe_class`` and register it on the
    default registry.

    Usage::

        @register_probe
        class MyProbe:
            layer_id = "service.containers"
            ...
    """

    def wrapper(*args, **kwargs) -> Probe:
        instance = probe_class(*args, **kwargs)
        _default_registry.register(instance)
        return instance

    return wrapper
