"""Adaptive scanner — follows up on anomalies with secondary probes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from opstree._version import __version__
from opstree.layers.tree import LayerTree
from opstree.probes.base import Probe, ProbeContext
from opstree.scanner.linear import LinearScanner
from opstree.snapshot.model import Snapshot, LayerData


class AdaptiveScanner(LinearScanner):
    """Scanner that runs follow-up probes when anomalies are detected.

    Inherits layer-tree walking from :class:`LinearScanner` and adds a
    ``followup_registry`` mapping *trigger layer* → list of follow-up
    :class:`Probe` objects.  After a primary probe reports anomalies,
    every follow-up registered for that layer is asked ``can_probe``;
    if it answers ``True`` it is scanned and its result is added to the
    snapshot as a new layer.

    This keeps anomaly detection in the primary probe (lightweight,
    same pass) and reconciliation / deep-dive logic in follow-ups
    (heavy, run only when needed).
    """

    def __init__(self, layer_tree: LayerTree):
        super().__init__(layer_tree)
        self.followup_registry: Dict[str, List[Probe]] = {}

    def register_followup(self, trigger_layer: str, probe: Probe) -> None:
        """Register *probe* to run when *trigger_layer* reports anomalies."""
        self.followup_registry.setdefault(trigger_layer, []).append(probe)

    def scan(self, target: str, execute: callable) -> Snapshot:
        """Scan all layers, then run follow-ups for every anomaly."""
        ctx = ProbeContext(target=target, execute=execute)

        layers: Dict[str, LayerData] = {}
        anomalies: List[dict] = []

        for layer_id in self.layer_tree.topological_order():
            probes = self.probe_registry.get(layer_id)
            if not probes:
                continue

            for probe in probes:
                if probe.can_probe(ctx):
                    result = probe.scan(ctx)
                    if result.success:
                        layers[layer_id] = result.layer_data
                        layer_anomalies = probe.anomalies(result.layer_data)
                        anomalies.extend(layer_anomalies)

                        # ── follow-up probes ─────────────────────────
                        if layer_anomalies:
                            for followup in self.followup_registry.get(layer_id, []):
                                if followup.can_probe(ctx):
                                    fu_result = followup.scan(ctx)
                                    if fu_result.success:
                                        layers[followup.layer_id] = fu_result.layer_data
                                        fu_anomalies = followup.anomalies(
                                            fu_result.layer_data
                                        )
                                        anomalies.extend(fu_anomalies)
                    break

        return Snapshot(
            target=target,
            scanned_at=datetime.now(timezone.utc),
            scanner_version=__version__,
            layers=layers,
            anomalies=anomalies,
        )
