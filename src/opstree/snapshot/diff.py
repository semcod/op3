"""Snapshot diff utilities."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal
from opstree.snapshot.model import Snapshot


@dataclass(frozen=True)
class Change:
    """Represents a single change between two snapshots."""

    layer_id: str
    path: str  # JMESPath-like path to the changed field
    type: Literal["added", "removed", "modified"]
    old_value: Any | None = None
    new_value: Any | None = None


def snapshot_diff(a: Snapshot, b: Snapshot) -> list[Change]:
    """Compare two snapshots and return a list of changes.

    Args:
        a: First snapshot (old state)
        b: Second snapshot (new state)

    Returns:
        List of Change objects representing differences
    """
    changes = []

    # Check for added/removed layers
    a_layers = set(a.layers.keys())
    b_layers = set(b.layers.keys())

    for layer_id in b_layers - a_layers:
        changes.append(
            Change(layer_id=layer_id, path=f"layers.{layer_id}", type="added")
        )

    for layer_id in a_layers - b_layers:
        changes.append(
            Change(layer_id=layer_id, path=f"layers.{layer_id}", type="removed")
        )

    # Compare common layers
    for layer_id in a_layers & b_layers:
        layer_changes = _diff_layer_data(a.layers[layer_id], b.layers[layer_id])
        changes.extend(layer_changes)

    return changes


def _diff_layer_data(a_layer, b_layer) -> list[Change]:
    """Diff two LayerData objects."""
    changes = []
    a_data = a_layer.data
    b_data = b_layer.data

    # Simple recursive diff for dicts
    def _diff_recursive(path: str, old: Any, new: Any) -> None:
        if isinstance(old, dict) and isinstance(new, dict):
            old_keys = set(old.keys())
            new_keys = set(new.keys())

            for key in new_keys - old_keys:
                changes.append(
                    Change(
                        layer_id=a_layer.layer_id,
                        path=f"{path}.{key}",
                        type="added",
                        new_value=new[key],
                    )
                )

            for key in old_keys - new_keys:
                changes.append(
                    Change(
                        layer_id=a_layer.layer_id,
                        path=f"{path}.{key}",
                        type="removed",
                        old_value=old[key],
                    )
                )

            for key in old_keys & new_keys:
                _diff_recursive(f"{path}.{key}", old[key], new[key])
        elif old != new:
            changes.append(
                Change(
                    layer_id=a_layer.layer_id,
                    path=path,
                    type="modified",
                    old_value=old,
                    new_value=new,
                )
            )

    _diff_recursive("data", a_data, b_data)
    return changes
