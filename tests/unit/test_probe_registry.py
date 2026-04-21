"""Unit tests for :class:`opstree.ProbeRegistry` and the module-level
default registry.

Regression: 0.1.7 defined ``register``/``get``/``all`` as classmethods,
which silently shared state across all :class:`ProbeRegistry` instances.
Callers that set ``scanner.probe_registry = my_registry`` were getting
the global registry regardless.
"""
from __future__ import annotations

import pytest

from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.probes.registry import (
    ProbeRegistry,
    _default_registry,
    get_default_registry,
    register_probe,
)
from opstree.snapshot.model import LayerData


# ── minimal Probe for testing ─────────────────────────────────────────────


class _DummyProbe:
    """Bare-minimum structural probe used throughout this file."""

    def __init__(self, layer_id: str, name: str = "dummy"):
        self.layer_id = layer_id
        self.probe_name = name

    def can_probe(self, ctx):  # pragma: no cover — trivial
        return True

    def scan(self, ctx):  # pragma: no cover — not used here
        from datetime import datetime, timezone
        return ProbeResult(
            layer_data=LayerData(
                layer_id=self.layer_id,
                probed_at=datetime.now(timezone.utc),
                probed_by=self.probe_name,
                data={},
                raw_evidence={},
            ),
            success=True,
        )

    def anomalies(self, data):  # pragma: no cover — trivial
        return []


# ── instance isolation ────────────────────────────────────────────────────


def test_registry_instances_are_isolated():
    """Two :class:`ProbeRegistry` instances must not share probe state.

    This is the property that was broken in 0.1.7.
    """
    a = ProbeRegistry()
    b = ProbeRegistry()

    a.register(_DummyProbe("service.containers", "a"))
    assert a.get("service.containers"), "probe must land in registry 'a'"
    assert not b.get("service.containers"), (
        "registry 'b' must not see probes registered on 'a' "
        "(got a shared global dict — classmethod regression)"
    )


def test_register_appends_multiple_probes_for_same_layer():
    r = ProbeRegistry()
    p1, p2 = _DummyProbe("os.kernel", "p1"), _DummyProbe("os.kernel", "p2")
    r.register(p1)
    r.register(p2)
    assert r.get("os.kernel") == [p1, p2]


def test_get_returns_empty_list_for_unknown_layer():
    r = ProbeRegistry()
    assert r.get("does.not.exist") == []


def test_get_returns_copy_so_mutation_doesnt_leak():
    r = ProbeRegistry()
    r.register(_DummyProbe("os.kernel"))
    returned = r.get("os.kernel")
    returned.append(_DummyProbe("os.kernel", "sneaky"))
    assert len(r.get("os.kernel")) == 1, (
        "ProbeRegistry.get must return a copy; mutating it leaked"
    )


def test_all_returns_deep_copy():
    r = ProbeRegistry()
    r.register(_DummyProbe("os.kernel"))
    snap = r.all()
    snap["os.kernel"].append(_DummyProbe("os.kernel", "sneaky"))
    assert len(r.get("os.kernel")) == 1


def test_clear_empties_registry():
    r = ProbeRegistry()
    r.register(_DummyProbe("os.kernel"))
    r.clear()
    assert r.all() == {}


# ── default registry + decorator ─────────────────────────────────────────


def test_get_default_registry_returns_module_singleton():
    assert get_default_registry() is _default_registry


def test_register_probe_decorator_uses_default_registry():
    """The ``@register_probe`` decorator must instantiate and push the
    probe onto the module-level default registry."""
    default = get_default_registry()
    default.clear()

    @register_probe
    class MyProbe(_DummyProbe):
        def __init__(self):
            super().__init__("endpoint.http", "decorated")

    MyProbe()  # instantiate — decorator wrapper registers as a side-effect

    probes = default.get("endpoint.http")
    assert len(probes) == 1
    assert probes[0].probe_name == "decorated"

    default.clear()  # clean up for other tests


def test_decorator_does_not_pollute_user_registries():
    """Probes registered via the decorator must NOT appear in a freshly
    constructed ProbeRegistry — that's the whole point of the fix."""
    default = get_default_registry()
    default.clear()

    @register_probe
    class NoiseProbe(_DummyProbe):
        def __init__(self):
            super().__init__("service.containers", "noise")

    NoiseProbe()

    user_registry = ProbeRegistry()
    assert user_registry.get("service.containers") == []

    default.clear()
