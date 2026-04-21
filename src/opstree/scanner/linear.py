"""Linear scanner — simple sequential layer scanning."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Optional
from opstree.layers.tree import LayerTree
from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.probes.registry import ProbeRegistry
from opstree.snapshot.model import Snapshot, LayerData


class LinearScanner:
    """Simple scanner that processes layers in topological order."""
    
    def __init__(self, layer_tree: LayerTree):
        self.layer_tree = layer_tree
        self.probe_registry = ProbeRegistry()
    
    def scan(self, target: str, execute: callable) -> Snapshot:
        """Scan all layers and return a complete snapshot."""
        ctx = ProbeContext(target=target, execute=execute)
        
        layers: Dict[str, LayerData] = {}
        anomalies = []
        
        for layer_id in self.layer_tree.topological_order():
            probes = self.probe_registry.get(layer_id)
            
            if not probes:
                continue  # No probes for this layer
            
            # Use the first available probe that can probe
            for probe in probes:
                if probe.can_probe(ctx):
                    result = probe.scan(ctx)
                    if result.success:
                        layers[layer_id] = result.layer_data
                        layer_anomalies = probe.anomalies(result.layer_data)
                        anomalies.extend(layer_anomalies)
                    break
        
        return Snapshot(
            target=target,
            scanned_at=datetime.now(timezone.utc),
            scanner_version="0.1.12",
            layers=layers,
            anomalies=anomalies,
        )


def scan_device(target: str, execute: callable, layer_tree: LayerTree) -> Snapshot:
    """Convenience function to scan a device."""
    scanner = LinearScanner(layer_tree)
    return scanner.scan(target, execute)
