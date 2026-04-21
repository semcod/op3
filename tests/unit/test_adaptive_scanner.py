"""Tests for :class:`AdaptiveScanner` and follow-up probes."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from opstree.layers.tree import LayerTree
from opstree.layers.builtin import PhysicalLayer, RuntimeLayer
from opstree.probes.base import ProbeContext, ProbeResult
from opstree.probes.builtin.compositor import CompositorProbe, KanshiReconcileProbe
from opstree.probes.registry import ProbeRegistry
from opstree.scanner.adaptive import AdaptiveScanner
from opstree.snapshot.model import LayerData


class DummyProbe:
    """Primary probe that always reports an anomaly."""

    layer_id = "physical.display"
    probe_name = "dummy_physical"

    def __init__(self, anomaly: bool = True):
        self._anomaly = anomaly

    def can_probe(self, ctx: ProbeContext) -> bool:
        return True

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        return ProbeResult(
            layer_data=LayerData(
                layer_id=self.layer_id,
                probed_at=datetime.now(timezone.utc),
                probed_by=self.probe_name,
                data={"drm_outputs": [{"name": "card0-DSI-1", "status": "connected"}]},
            ),
            success=True,
        )

    def anomalies(self, data: LayerData) -> list:
        if self._anomaly:
            return [{
                "severity": "warning",
                "layer": self.layer_id,
                "message": "Both DSI and HDMI connected",
                "evidence": {},
            }]
        return []


class FollowUpProbe:
    """Follow-up probe triggered by physical.display anomaly."""

    layer_id = "runtime.compositor.kanshi"
    probe_name = "followup_kanshi"

    def __init__(self, can: bool = True):
        self._can = can

    def can_probe(self, ctx: ProbeContext) -> bool:
        return self._can

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        return ProbeResult(
            layer_data=LayerData(
                layer_id=self.layer_id,
                probed_at=datetime.now(timezone.utc),
                probed_by=self.probe_name,
                data={"reconcile_needed": True},
            ),
            success=True,
        )

    def anomalies(self, data: LayerData) -> list:
        return []


def _noop_execute(cmd: str):
    return "", "", 0


class TestAdaptiveScanner:
    def test_no_anomaly_means_no_followup(self):
        tree = LayerTree()
        tree.register(PhysicalLayer.display)

        scanner = AdaptiveScanner(tree)
        scanner.probe_registry.register(DummyProbe(anomaly=False))

        followup = FollowUpProbe()
        scanner.register_followup("physical.display", followup)

        snapshot = scanner.scan("t1", _noop_execute)

        assert "physical.display" in snapshot.layers
        assert "runtime.compositor.kanshi" not in snapshot.layers
        assert snapshot.anomalies == []

    def test_anomaly_triggers_followup(self):
        tree = LayerTree()
        tree.register(PhysicalLayer.display)

        scanner = AdaptiveScanner(tree)
        scanner.probe_registry.register(DummyProbe(anomaly=True))

        followup = FollowUpProbe()
        scanner.register_followup("physical.display", followup)

        snapshot = scanner.scan("t1", _noop_execute)

        assert "physical.display" in snapshot.layers
        assert "runtime.compositor.kanshi" in snapshot.layers
        assert any(
            a["layer"] == "physical.display" for a in snapshot.anomalies
        )

    def test_followup_skipped_when_can_probe_false(self):
        tree = LayerTree()
        tree.register(PhysicalLayer.display)

        scanner = AdaptiveScanner(tree)
        scanner.probe_registry.register(DummyProbe(anomaly=True))

        followup = FollowUpProbe(can=False)
        scanner.register_followup("physical.display", followup)

        snapshot = scanner.scan("t1", _noop_execute)

        assert "runtime.compositor.kanshi" not in snapshot.layers

    def test_followup_anomalies_propagated(self):
        tree = LayerTree()
        tree.register(PhysicalLayer.display)

        scanner = AdaptiveScanner(tree)
        scanner.probe_registry.register(DummyProbe(anomaly=True))

        class AnomalyFollowUp:
            layer_id = "runtime.compositor.kanshi"
            probe_name = "followup_anomaly"

            def can_probe(self, ctx: ProbeContext) -> bool:
                return True

            def scan(self, ctx: ProbeContext) -> ProbeResult:
                return ProbeResult(
                    layer_data=LayerData(
                        layer_id=self.layer_id,
                        probed_at=datetime.now(timezone.utc),
                        probed_by=self.probe_name,
                        data={},
                    ),
                    success=True,
                )

            def anomalies(self, data: LayerData) -> list:
                return [{
                    "severity": "info",
                    "layer": self.layer_id,
                    "message": "follow-up anomaly",
                    "evidence": {},
                }]

        scanner.register_followup("physical.display", AnomalyFollowUp())
        snapshot = scanner.scan("t1", _noop_execute)

        assert any(
            a["layer"] == "runtime.compositor.kanshi"
            for a in snapshot.anomalies
        )


class TestCompositorProbe:
    def test_kanshi_not_installed(self):
        probe = CompositorProbe()
        ctx = ProbeContext(target="t", execute=lambda cmd: ("", "", 1))
        assert probe.can_probe(ctx) is False

    def test_kanshi_installed(self):
        probe = CompositorProbe()
        # which kanshi succeeds, wayland socket absent.
        ctx = ProbeContext(
            target="t",
            execute=lambda cmd: (
                ("/usr/bin/kanshi", "", 0) if "which kanshi" in cmd else ("", "", 1)
            ),
        )
        assert probe.can_probe(ctx) is True

    def test_scan_returns_layer_data(self):
        probe = CompositorProbe()

        responses = {
            "which kanshi 2>/dev/null": ("/usr/bin/kanshi", "", 0),
            "ls /run/user/$(id -u)/ 2>/dev/null | grep '^wayland-'": ("wayland-0", "", 0),
            "pgrep -x 'labwc' 2>/dev/null": ("1234", "", 0),
            "labwc --version 2>/dev/null": ("labwc 0.7.0", "", 0),
            "cat ~/.config/kanshi/config 2>/dev/null": (
                "dual-display {\noutput card0-DSI-1 enable\n}", "", 0
            ),
            "ps -o args= -p $(pgrep -x kanshi) 2>/dev/null": ("", "", 1),
        }

        def execute(cmd: str):
            for pattern, result in responses.items():
                if pattern in cmd:
                    return result
            return "", "", 1

        ctx = ProbeContext(target="t", execute=execute)
        result = probe.scan(ctx)
        assert result.success
        assert result.layer_data.data["compositor"] == "labwc"
        assert result.layer_data.data["kanshi_enabled"] is True
        assert len(result.layer_data.data["kanshi_profiles"]) == 1

    def test_anomalies_when_no_active_profile(self):
        probe = CompositorProbe()
        layer = LayerData(
            layer_id="runtime.compositor",
            probed_at=datetime.now(timezone.utc),
            probed_by="test",
            data={
                "compositor": "labwc",
                "kanshi_enabled": True,
                "kanshi_profiles": [],
                "active_profile": None,
            },
        )
        anomalies = probe.anomalies(layer)
        assert len(anomalies) == 1
        assert "no active profile" in anomalies[0]["message"]


class TestKanshiReconcileProbe:
    def test_suggests_profile_when_dsi_and_hdmi_present(self):
        probe = KanshiReconcileProbe()

        responses = {
            "which kanshi 2>/dev/null": ("/usr/bin/kanshi", "", 0),
            "ls /sys/class/drm/ 2>/dev/null | grep '^card[0-9]-'": (
                "card0-DSI-1\ncard1-HDMI-A-1", "", 0
            ),
        }

        def execute(cmd: str):
            for pattern, result in responses.items():
                if pattern in cmd:
                    return result
            return "", "", 1

        ctx = ProbeContext(target="t", execute=execute)
        result = probe.scan(ctx)
        assert result.success
        assert result.layer_data.data["reconcile_needed"] is True
        profile = result.layer_data.data["suggested_profile"]
        assert profile is not None
        assert profile["name"] == "dual-display"

    def test_no_suggestion_without_dual_output(self):
        probe = KanshiReconcileProbe()

        responses = {
            "which kanshi 2>/dev/null": ("/usr/bin/kanshi", "", 0),
            "ls /sys/class/drm/ 2>/dev/null | grep '^card[0-9]-'": (
                "card0-DSI-1", "", 0
            ),
        }

        def execute(cmd: str):
            for pattern, result in responses.items():
                if pattern in cmd:
                    return result
            return "", "", 1

        ctx = ProbeContext(target="t", execute=execute)
        result = probe.scan(ctx)
        assert result.layer_data.data["reconcile_needed"] is False
        assert result.layer_data.data["suggested_profile"] is None
