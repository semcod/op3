"""Tests for :func:`opstree.build_scanner` / :func:`build_layer_tree`.

The goal of these helpers is to replace the ~20 lines of boilerplate
every consumer (doql, redeploy, …) used to duplicate:

    tree = LayerTree()
    tree.register(PhysicalLayer.compute)
    tree.register(OsLayer.kernel)
    tree.register(...)
    registry = ProbeRegistry()
    registry.register(OsKernelProbe())
    ...
    scanner = LinearScanner(tree)
    scanner.probe_registry = registry

After the fix that boilerplate collapses to a single ``build_scanner(...)``
call with automatic dependency resolution.
"""
from __future__ import annotations

import pytest

from opstree import build_layer_tree, build_scanner
from opstree.probes.context import ExecuteResult, MockContext
from opstree.probes.registry import ProbeRegistry


# ── layer tree ────────────────────────────────────────────────────────────


def test_build_layer_tree_registers_requested_leaf():
    tree = build_layer_tree(["service.containers"])
    order = tree.topological_order()
    assert "service.containers" in order


def test_build_layer_tree_pulls_transitive_dependencies():
    """service.containers depends on runtime.container depends on
    os.kernel depends on physical.compute — all must be present."""
    tree = build_layer_tree(["service.containers"])
    order = tree.topological_order()
    for required in ("physical.compute", "os.kernel", "runtime.container",
                     "service.containers"):
        assert required in order, (
            f"Expected transitive dep {required!r} to be registered, "
            f"got order={order}"
        )


def test_build_layer_tree_orders_deps_before_dependents():
    tree = build_layer_tree(["service.containers"])
    order = tree.topological_order()
    # A layer must appear after each of its direct dependencies.
    assert order.index("os.kernel") < order.index("runtime.container")
    assert order.index("runtime.container") < order.index("service.containers")


def test_build_layer_tree_rejects_unknown_layer():
    with pytest.raises(ValueError, match="Unknown built-in layer id"):
        build_layer_tree(["nonexistent.layer"])


def test_build_layer_tree_deduplicates_shared_dependencies():
    """Requesting two leaves that share a dependency chain must not
    register the same layer twice (``LayerTree.register`` raises on dupe)."""
    tree = build_layer_tree(["service.containers", "endpoint.http"])
    order = tree.topological_order()
    # os.kernel is in the ancestry of both — must appear exactly once.
    assert order.count("os.kernel") == 1


# ── scanner factory ───────────────────────────────────────────────────────


def test_build_scanner_uses_isolated_registry():
    """Each ``build_scanner`` call must produce its own registry so that
    repeated calls in the same process don't accumulate probes."""
    s1 = build_scanner(["os.kernel"])
    s2 = build_scanner(["os.kernel"])
    assert s1.probe_registry is not s2.probe_registry


def test_build_scanner_registry_not_shared_with_default():
    """A scanner's registry must not be the module-level default — that
    would re-introduce the 0.1.7 bug."""
    from opstree.probes.registry import get_default_registry

    scanner = build_scanner(["os.kernel"])
    assert scanner.probe_registry is not get_default_registry()


def test_build_scanner_populates_probes_for_requested_layers():
    scanner = build_scanner(["service.containers"])
    assert scanner.probe_registry.get("service.containers"), (
        "default ServiceContainersProbe should be registered"
    )
    assert scanner.probe_registry.get("runtime.container"), (
        "transitively-required RuntimeContainerProbe should be registered"
    )


def test_build_scanner_include_default_probes_false_leaves_registry_empty():
    scanner = build_scanner(["os.kernel"], include_default_probes=False)
    assert scanner.probe_registry.all() == {}


def test_build_scanner_extra_probes_are_appended():
    """Extra probes coexist with the defaults (built-ins run first)."""

    class _ExtraProbe:
        """Minimal structural probe matching the ``Probe`` Protocol."""
        layer_id = "os.kernel"
        probe_name = "custom"

        def can_probe(self, ctx):  # pragma: no cover — not invoked here
            return False

        def scan(self, ctx):  # pragma: no cover
            raise NotImplementedError

        def anomalies(self, data):  # pragma: no cover
            return []

    extra = _ExtraProbe()
    scanner = build_scanner(["os.kernel"], extra_probes={"os.kernel": [extra]})

    probes = scanner.probe_registry.get("os.kernel")
    # Default OsKernelProbe first, then our custom one.
    assert len(probes) == 2
    assert probes[-1] is extra


# ── end-to-end: actually scan a mocked host ───────────────────────────────


def test_build_scanner_end_to_end_scan():
    responses = {
        "which docker": ExecuteResult("/usr/bin/docker", "", 0),
        "which podman": ExecuteResult("", "", 1),
        "docker --version 2>/dev/null": ExecuteResult("Docker version 24.0.7", "", 0),
        "podman --version 2>/dev/null": ExecuteResult("", "", 1),
        "docker ps -a --format json 2>/dev/null": ExecuteResult("[]", "", 0),
        "podman ps -a --format json 2>/dev/null": ExecuteResult("", "", 1),
        "which systemctl": ExecuteResult("/bin/systemctl", "", 0),
        "systemctl list-units --type=service --all --no-legend 2>/dev/null":
            ExecuteResult("nginx.service loaded active running nginx\n", "", 0),
        "systemctl is-enabled nginx.service 2>/dev/null":
            ExecuteResult("enabled", "", 0),
    }

    ctx = MockContext(responses=responses)
    scanner = build_scanner(["service.containers"])
    snapshot = scanner.scan("mock@device", ctx.execute)

    assert "service.containers" in snapshot.layers
    services = snapshot.layers["service.containers"].data["systemd_services"]
    assert any(s["name"] == "nginx.service" for s in services)


def test_build_scanner_does_not_leak_into_subsequent_calls():
    """Regression guard: after build_scanner registers probes, a *fresh*
    ProbeRegistry() must still be empty. The class-level state bug made
    this fail."""
    build_scanner(["service.containers"])
    fresh = ProbeRegistry()
    assert fresh.all() == {}, (
        "build_scanner leaked into a freshly-constructed ProbeRegistry — "
        "the class-level _probes dict is being mutated again"
    )
