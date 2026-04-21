"""Tests for :mod:`opstree.fleet.formats` (A1)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from opstree import __version__, render_common_as_snapshot, render_variant_matrix
from opstree.fleet import FleetSnapshot, FleetVariance
from opstree.fleet.scanner import compute_variance
from opstree.snapshot.model import LayerData, Snapshot


def _snapshot(target: str, *, kernel: str = "6.1.0", resolution=None) -> Snapshot:
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


class TestRenderCommonAsSnapshot:
    def test_empty_fleet(self):
        fleet = FleetSnapshot(targets=[], snapshots={}, variance=FleetVariance())
        common = render_common_as_snapshot(fleet)
        assert common.target == "fleet:common"
        assert common.layers == {}

    def test_identical_fleet_returns_all_fields(self):
        snaps = {
            "pi1": _snapshot("pi1", kernel="6.1.0"),
            "pi2": _snapshot("pi2", kernel="6.1.0"),
        }
        variance = compute_variance(snaps)
        fleet = FleetSnapshot(targets=["pi1", "pi2"], snapshots=snaps, variance=variance)
        common = render_common_as_snapshot(fleet)
        assert "os.kernel" in common.layers
        assert common.layers["os.kernel"].data["version"] == "6.1.0"
        assert common.layers["os.kernel"].data["arch"] == "aarch64"

    def test_divergent_fields_omitted(self):
        snaps = {
            "pi1": _snapshot("pi1", kernel="6.1.0", resolution="1920x1080"),
            "pi2": _snapshot("pi2", kernel="6.6.20", resolution="1280x720"),
        }
        variance = compute_variance(snaps)
        fleet = FleetSnapshot(targets=["pi1", "pi2"], snapshots=snaps, variance=variance)
        common = render_common_as_snapshot(fleet)
        # version diverges → omitted
        assert "version" not in common.layers.get("os.kernel", {}).data
        # resolution diverges → omitted
        assert "resolution" not in common.layers.get("physical.display", {}).data
        # arch is uniform → kept
        assert common.layers["os.kernel"].data.get("arch") == "aarch64"
        # enabled is uniform → kept
        assert common.layers["physical.display"].data.get("enabled") is True


class TestRenderVariantMatrix:
    def test_empty_fleet(self):
        fleet = FleetSnapshot(targets=[], snapshots={}, variance=FleetVariance())
        matrix = render_variant_matrix(fleet)
        assert matrix == {"common": {}, "variants": {}}

    def test_shows_divergent_paths(self):
        snaps = {
            "pi1": _snapshot("pi1", kernel="6.1.0"),
            "pi2": _snapshot("pi2", kernel="6.6.20"),
        }
        variance = compute_variance(snaps)
        fleet = FleetSnapshot(targets=["pi1", "pi2"], snapshots=snaps, variance=variance)
        matrix = render_variant_matrix(fleet)
        assert "os.kernel.data.version" in matrix["variants"]
        assert matrix["variants"]["os.kernel.data.version"] == {"pi1": "6.1.0", "pi2": "6.6.20"}
        # arch is common
        assert "os.kernel.data.arch" in matrix["common"]
