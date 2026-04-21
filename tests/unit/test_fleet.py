"""Tests for :mod:`opstree.fleet` — fleet scanning + variance.

The fleet module introduces two behaviours that need coverage:

* :func:`scan_fleet` runs one scanner against many targets and bundles
  the results.
* :func:`compute_variance` deterministically identifies every field
  that disagrees across a fleet, regardless of snapshot insertion
  order.

The tests below exercise both with synthetic snapshots and with a real
:class:`LinearScanner` driven by :class:`MockContext` so we get
end-to-end coverage of the thread pool + per-target ``execute``
plumbing.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from opstree import __version__, build_scanner, compute_variance, scan_fleet
from opstree.fleet import FleetSnapshot, FleetVariance
from opstree.probes.context import ExecuteResult, MockContext
from opstree.snapshot.model import LayerData, Snapshot


# ── helpers ───────────────────────────────────────────────────────────────


def _snapshot(target: str, *, kernel: str = "6.1.0", resolution=None) -> Snapshot:
    """Build a two-layer synthetic snapshot for variance tests.

    Kept tiny so assertion failures point at what actually differs
    rather than swimming through realistic probe payloads.
    """
    layers = {
        "os.kernel": LayerData(
            layer_id="os.kernel",
            probed_at=datetime.now(timezone.utc),
            probed_by="test",
            data={"version": kernel, "arch": "aarch64"},
        ),
    }
    if resolution is not None:
        layers["physical.display"] = LayerData(
            layer_id="physical.display",
            probed_at=datetime.now(timezone.utc),
            probed_by="test",
            data={"resolution": resolution, "enabled": True},
        )
    return Snapshot(
        target=target,
        scanned_at=datetime.now(timezone.utc),
        scanner_version=__version__,
        layers=layers,
    )


# ── compute_variance ──────────────────────────────────────────────────────


def test_compute_variance_empty_returns_uniform():
    variance = compute_variance({})
    assert variance.is_uniform
    assert variance.fields == {}


def test_compute_variance_single_snapshot_is_uniform():
    """With only one target there's nothing to diverge against."""
    variance = compute_variance({"pi1": _snapshot("pi1")})
    assert variance.is_uniform


def test_compute_variance_identical_fleet_has_no_fields():
    snaps = {
        "pi1": _snapshot("pi1", kernel="6.1.0"),
        "pi2": _snapshot("pi2", kernel="6.1.0"),
        "pi3": _snapshot("pi3", kernel="6.1.0"),
    }
    variance = compute_variance(snaps)
    assert variance.is_uniform
    assert variance.by_layer == {}


def test_compute_variance_records_single_field_divergence():
    snaps = {
        "pi1": _snapshot("pi1", kernel="6.1.0"),
        "pi2": _snapshot("pi2", kernel="6.1.0"),
        "pi3": _snapshot("pi3", kernel="6.6.20"),
    }
    variance = compute_variance(snaps)
    assert not variance.is_uniform
    assert "os.kernel.data.version" in variance.fields
    diverged = variance.fields["os.kernel.data.version"]
    assert diverged == {"pi1": "6.1.0", "pi2": "6.1.0", "pi3": "6.6.20"}
    # arch is identical → must NOT appear
    assert "os.kernel.data.arch" not in variance.fields


def test_compute_variance_counts_diverging_fields_per_layer():
    snaps = {
        "pi1": _snapshot("pi1", kernel="6.1.0", resolution="1920x1080"),
        "pi2": _snapshot("pi2", kernel="6.6.20", resolution="1280x720"),
    }
    variance = compute_variance(snaps)
    # One field diverges in each layer.
    assert variance.by_layer == {"os.kernel": 1, "physical.display": 1}


def test_compute_variance_records_missing_layer_as_none():
    """If one host lacks a layer entirely the missing side shows as None."""
    snaps = {
        "pi1": _snapshot("pi1", resolution="1920x1080"),
        "pi2": _snapshot("pi2"),  # no physical.display
    }
    variance = compute_variance(snaps)
    # Every path under physical.display should show pi2 as None.
    display_paths = [p for p in variance.fields if p.startswith("physical.display")]
    assert display_paths, "expected physical.display paths to be flagged as diverging"
    for path in display_paths:
        assert variance.fields[path]["pi2"] is None


def test_compute_variance_is_order_independent():
    """Swapping the snapshot insertion order must yield identical fields."""
    a = _snapshot("pi1", kernel="6.1.0")
    b = _snapshot("pi2", kernel="6.6.20")
    forward = compute_variance({"pi1": a, "pi2": b})
    reverse = compute_variance({"pi2": b, "pi1": a})
    assert forward.fields == reverse.fields
    assert forward.by_layer == reverse.by_layer


def test_compute_variance_handles_nested_dict_equality():
    """Equal nested structures must not falsely register as diverging."""
    shared = {
        "version": "6.1.0",
        "arch": "aarch64",
        "modules": ["usb_storage", "ext4"],
    }
    s1 = Snapshot(
        target="pi1",
        scanned_at=datetime.now(timezone.utc),
        scanner_version=__version__,
        layers={
            "os.kernel": LayerData(
                layer_id="os.kernel",
                probed_at=datetime.now(timezone.utc),
                probed_by="test",
                data=shared,
            )
        },
    )
    s2 = Snapshot(
        target="pi2",
        scanned_at=datetime.now(timezone.utc),
        scanner_version=__version__,
        layers={
            "os.kernel": LayerData(
                layer_id="os.kernel",
                probed_at=datetime.now(timezone.utc),
                probed_by="test",
                data=dict(shared),  # identical content, different object
            )
        },
    )
    variance = compute_variance({"pi1": s1, "pi2": s2})
    assert variance.is_uniform


# ── scan_fleet ────────────────────────────────────────────────────────────


def _kernel_responses(version: str) -> dict[str, ExecuteResult]:
    """Minimal mock responses for the builtin os.kernel probe."""
    return {
        # can_probe gate — must report a Linux system
        "uname -s": ExecuteResult("Linux", "", 0),
        "uname -r": ExecuteResult(version, "", 0),
        "uname -m": ExecuteResult("aarch64", "", 0),
        "hostname": ExecuteResult("mock-host", "", 0),
        "cat /proc/uptime": ExecuteResult("12345.67 10000.00", "", 0),
    }


def test_scan_fleet_empty_returns_empty_fleet_snapshot():
    scanner = build_scanner(["os.kernel"])
    fleet = scan_fleet(scanner, target_execute={})
    assert isinstance(fleet, FleetSnapshot)
    assert fleet.size == 0
    assert fleet.targets == []
    assert fleet.snapshots == {}
    assert fleet.variance.is_uniform


def test_scan_fleet_scans_each_target():
    scanner = build_scanner(["os.kernel"])
    target_execute = {
        "pi1": MockContext(_kernel_responses("6.1.0")).execute,
        "pi2": MockContext(_kernel_responses("6.1.0")).execute,
        "pi3": MockContext(_kernel_responses("6.6.20")).execute,
    }

    fleet = scan_fleet(scanner, target_execute)

    assert fleet.size == 3
    assert set(fleet.snapshots) == {"pi1", "pi2", "pi3"}
    # Per-target snapshot is well-formed.
    for target, snap in fleet.snapshots.items():
        assert snap.target == target
        assert snap.scanner_version == __version__
        assert "os.kernel" in snap.layers


def test_scan_fleet_preserves_iteration_order_in_targets():
    scanner = build_scanner(["os.kernel"])
    target_execute = {
        "pi2": MockContext(_kernel_responses("6.1.0")).execute,
        "pi1": MockContext(_kernel_responses("6.1.0")).execute,
        "pi3": MockContext(_kernel_responses("6.1.0")).execute,
    }
    fleet = scan_fleet(scanner, target_execute)
    # ``targets`` follows caller ordering regardless of which thread finished first.
    assert fleet.targets == ["pi2", "pi1", "pi3"]


def test_scan_fleet_detects_drifted_kernel():
    scanner = build_scanner(["os.kernel"])
    target_execute = {
        "pi1": MockContext(_kernel_responses("6.1.0")).execute,
        "pi2": MockContext(_kernel_responses("6.1.0")).execute,
        "pi3": MockContext(_kernel_responses("6.6.20")).execute,
    }
    fleet = scan_fleet(scanner, target_execute)

    assert not fleet.variance.is_uniform
    assert "os.kernel.data.version" in fleet.variance.fields
    row = fleet.variance.fields["os.kernel.data.version"]
    assert row["pi1"] == row["pi2"] == "6.1.0"
    assert row["pi3"] == "6.6.20"


def test_scan_fleet_uniform_when_all_hosts_identical():
    scanner = build_scanner(["os.kernel"])
    target_execute = {
        f"pi{i}": MockContext(_kernel_responses("6.1.0")).execute
        for i in range(1, 5)
    }
    fleet = scan_fleet(scanner, target_execute)
    assert fleet.variance.is_uniform


def test_scan_fleet_propagates_scanner_failure():
    """Per-target exceptions surface to the caller — no silent fleet corruption."""
    scanner = build_scanner(["os.kernel"])

    def boom(cmd: str):
        raise RuntimeError(f"transport exploded on {cmd}")

    target_execute = {
        "pi1": MockContext(_kernel_responses("6.1.0")).execute,
        "pi_bad": boom,
    }
    with pytest.raises(RuntimeError, match="transport exploded"):
        scan_fleet(scanner, target_execute)


def test_fleet_snapshot_for_target_lookup():
    scanner = build_scanner(["os.kernel"])
    target_execute = {
        "pi1": MockContext(_kernel_responses("6.1.0")).execute,
    }
    fleet = scan_fleet(scanner, target_execute)
    assert fleet.for_target("pi1") is fleet.snapshots["pi1"]
    assert fleet.for_target("not-there") is None
