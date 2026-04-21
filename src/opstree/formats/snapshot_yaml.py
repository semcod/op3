"""Snapshot YAML format adapter — native op3 snapshot format."""
from __future__ import annotations
from typing import Any, Dict
from opstree.snapshot.model import Snapshot, PartialSnapshot, LayerData
from datetime import datetime
import yaml


class SnapshotYamlAdapter:
    """Native op3 snapshot format adapter."""
    format_name = "snapshot_yaml"
    
    def parse(self, text: str) -> Snapshot:
        """Parsuj snapshot.yaml → Snapshot."""
        data = yaml.safe_load(text)
        
        # Convert layer data
        layers = {}
        for layer_id, layer_data in data.get("layers", {}).items():
            layers[layer_id] = LayerData(
                layer_id=layer_id,
                probed_at=datetime.fromisoformat(layer_data.get("probed_at", datetime.utcnow().isoformat())),
                probed_by=layer_data.get("probed_by", "unknown"),
                data=layer_data.get("data", {}),
                raw_evidence=layer_data.get("raw_evidence", {}),
            )
        
        return Snapshot(
            target=data.get("target", "unknown"),
            scanned_at=datetime.fromisoformat(data.get("scanned_at", datetime.utcnow().isoformat())),
            scanner_version=data.get("scanner_version", "0.1.2"),
            layers=layers,
            anomalies=data.get("anomalies", []),
        )
    
    def render(self, snapshot: Snapshot | PartialSnapshot) -> str:
        """Renderuj Snapshot → snapshot.yaml."""
        data = {
            "target": snapshot.target,
            "scanned_at": snapshot.scanned_at.isoformat() if hasattr(snapshot, "scanned_at") else datetime.utcnow().isoformat(),
            "scanner_version": snapshot.scanner_version if hasattr(snapshot, "scanner_version") else "0.1.2",
            "layers": {},
        }
        
        for layer_id, layer_data in snapshot.layers.items():
            data["layers"][layer_id] = {
                "layer_id": layer_id,
                "probed_at": layer_data.probed_at.isoformat(),
                "probed_by": layer_data.probed_by,
                "data": layer_data.data,
                "raw_evidence": layer_data.raw_evidence,
            }
        
        if hasattr(snapshot, "anomalies"):
            data["anomalies"] = snapshot.anomalies
        
        return yaml.dump(data, sort_keys=False, default_flow_style=False)
