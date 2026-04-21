"""Fleet snapshot exporters."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from opstree.fleet.model import FleetSnapshot
from opstree.snapshot.model import LayerData, Snapshot
from opstree.fleet.scanner import _flatten_snapshot


def _unflatten(paths: dict[str, Any]) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    for path, value in paths.items():
        parts = path.split(".")
        if len(parts) < 3:
            continue
        # Paths from _flatten_snapshot are "<layer_id>.data.<...>"
        layer_id = f"{parts[0]}.{parts[1]}"
        rest = parts[3:]
        node = layers.setdefault(layer_id, {})
        for key in rest[:-1]:
            node = node.setdefault(key, {})
        if rest:
            node[rest[-1]] = value
    return layers


def render_common_as_snapshot(fleet: FleetSnapshot) -> Snapshot:
    if not fleet.snapshots:
        return Snapshot(target="fleet:common", scanned_at=datetime.now(timezone.utc),
                      scanner_version="opstree.fleet.formats", layers={})
    ref_target = fleet.targets[0]
    ref_flat = _flatten_snapshot(fleet.snapshots[ref_target])
    divergent = set(fleet.variance.fields.keys())
    common_flat = {p: v for p, v in ref_flat.items() if p not in divergent}
    layers_data = _unflatten(common_flat)
    layers: dict[str, LayerData] = {}
    for layer_id, data in layers_data.items():
        if not data:
            continue
        layers[layer_id] = LayerData(layer_id=layer_id, probed_at=datetime.now(timezone.utc),
                                      probed_by="fleet.formats", data=data)
    return Snapshot(target="fleet:common", scanned_at=datetime.now(timezone.utc),
                    scanner_version="opstree.fleet.formats", layers=layers)


def render_variant_matrix(fleet: FleetSnapshot) -> dict[str, Any]:
    if not fleet.snapshots:
        return {"common": {}, "variants": {}}
    ref_flat = _flatten_snapshot(fleet.snapshots[fleet.targets[0]])
    divergent = fleet.variance.fields
    common_flat = {p: v for p, v in ref_flat.items() if p not in divergent}
    return {
        "common": common_flat,
        "variants": {path: {tgt: values.get(tgt) for tgt in fleet.targets}
                     for path, values in divergent.items()},
    }
