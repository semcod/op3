"""High-level scanner factory.

The public :func:`build_scanner` wraps up the plumbing that every caller
used to replicate by hand (``LayerTree`` + ``ProbeRegistry`` + built-in
probes + transitive dependency resolution). Callers still needing
fine-grained control can instantiate :class:`LinearScanner` directly.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from opstree.layers.builtin import (
    BUSINESS_HEALTH,
    ENDPOINT_HTTP,
    ENDPOINT_TCP,
    OS_CONFIG,
    OS_KERNEL,
    PHYSICAL_COMPUTE,
    PHYSICAL_DISPLAY,
    PHYSICAL_NETWORK,
    RUNTIME_COMPOSITOR,
    RUNTIME_CONTAINER,
    SERVICE_CONTAINERS,
    SERVICE_SYSTEMD,
)
from opstree.layers.tree import LayerDefinition, LayerTree
from opstree.probes.base import Probe
from opstree.probes.builtin.business_health import BusinessHealthProbe
from opstree.probes.builtin.endpoint_http import EndpointHttpProbe
from opstree.probes.builtin.os_linux import OsConfigProbe, OsKernelProbe
from opstree.probes.builtin.physical_rpi import RpiPhysicalDisplayProbe
from opstree.probes.builtin.runtime_container import RuntimeContainerProbe
from opstree.probes.builtin.service_containers import ServiceContainersProbe
from opstree.probes.registry import ProbeRegistry
from opstree.scanner.linear import LinearScanner


# ── layer + probe tables ──────────────────────────────────────────────────

_BUILTIN_LAYERS: Dict[str, LayerDefinition] = {
    "physical.display": PHYSICAL_DISPLAY,
    "physical.network": PHYSICAL_NETWORK,
    "physical.compute": PHYSICAL_COMPUTE,
    "os.kernel": OS_KERNEL,
    "os.config": OS_CONFIG,
    "runtime.container": RUNTIME_CONTAINER,
    "runtime.compositor": RUNTIME_COMPOSITOR,
    "service.containers": SERVICE_CONTAINERS,
    "service.systemd": SERVICE_SYSTEMD,
    "endpoint.http": ENDPOINT_HTTP,
    "endpoint.tcp": ENDPOINT_TCP,
    "business.health": BUSINESS_HEALTH,
}


def _default_probe_factory(layer_id: str) -> List[Probe]:
    """Return fresh built-in probe instances for ``layer_id``.

    Returning new instances per call avoids the footgun where two
    scanners end up sharing a stateful probe.
    """
    return {
        "physical.display": [RpiPhysicalDisplayProbe()],
        "os.kernel": [OsKernelProbe()],
        "os.config": [OsConfigProbe()],
        "runtime.container": [RuntimeContainerProbe()],
        "service.containers": [ServiceContainersProbe()],
        "endpoint.http": [EndpointHttpProbe()],
        "business.health": [BusinessHealthProbe()],
    }.get(layer_id, [])


# ── dependency resolution ─────────────────────────────────────────────────


def _resolve_dependencies(layer_ids: Iterable[str]) -> List[str]:
    """Expand ``layer_ids`` to include all transitive ``depends_on``.

    :class:`LayerTree.topological_order` raises ``"Cycle detected"`` when
    a registered layer references an unregistered dependency (Kahn's
    algorithm stalls because the in-degree never reaches zero). Callers
    almost always want "register this leaf and everything it needs" — so
    this helper does exactly that, in topological order.
    """
    resolved: List[str] = []
    seen: set[str] = set()

    def _visit(lid: str) -> None:
        if lid in seen:
            return
        seen.add(lid)
        if lid not in _BUILTIN_LAYERS:
            raise ValueError(f"Unknown built-in layer id: {lid!r}")
        for dep in _BUILTIN_LAYERS[lid].depends_on:
            _visit(dep)
        resolved.append(lid)

    for lid in layer_ids:
        _visit(lid)
    return resolved


# ── public API ────────────────────────────────────────────────────────────


def build_layer_tree(layer_ids: Sequence[str]) -> LayerTree:
    """Build a :class:`LayerTree` containing ``layer_ids`` + their deps.

    Raises :class:`ValueError` for unknown layer ids so the caller can
    distinguish "typo" from "empty scan".
    """
    tree = LayerTree()
    for lid in _resolve_dependencies(layer_ids):
        tree.register(_BUILTIN_LAYERS[lid])
    return tree


def build_scanner(
    layer_ids: Sequence[str],
    *,
    extra_probes: Optional[Dict[str, List[Probe]]] = None,
    include_default_probes: bool = True,
) -> LinearScanner:
    """Return a fully-wired :class:`LinearScanner` for ``layer_ids``.

    Parameters
    ----------
    layer_ids:
        Leaf layer ids of interest. Transitive dependencies are added
        automatically via :func:`_resolve_dependencies`.
    extra_probes:
        Optional ``{layer_id: [probes]}`` mapping. Registered **after**
        the built-ins so callers can add custom probes alongside the
        defaults.
    include_default_probes:
        Set to ``False`` to skip the built-in probe set entirely — useful
        when the caller wants to drive a scan with their own probes only.

    The scanner's registry is a fresh :class:`ProbeRegistry` instance,
    so repeated calls are isolated from each other and from the
    module-level default registry.
    """
    tree = build_layer_tree(layer_ids)
    scanner = LinearScanner(tree)

    # Replace the default instance with a clean one so we don't inherit
    # anything the caller may have registered via ``register_probe``.
    registry = ProbeRegistry()
    scanner.probe_registry = registry

    for lid in tree.topological_order():
        if include_default_probes:
            for probe in _default_probe_factory(lid):
                registry.register(probe)
        if extra_probes and lid in extra_probes:
            for probe in extra_probes[lid]:
                registry.register(probe)

    return scanner


__all__ = [
    "build_layer_tree",
    "build_scanner",
]
