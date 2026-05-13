"""Data models for fleet-level snapshots.

``FleetSnapshot`` groups N individual :class:`Snapshot` instances with a
summary of fields that differ across them (``FleetVariance``).

Design notes
------------
* **Frozen.** Both models are immutable; mutate by constructing a new
  instance. Matches the policy of :class:`opstree.Snapshot`.
* **Variance is explicit, not derived.** The variance payload is stored
  in the model rather than recomputed on access because computing it
  from a large fleet is not free, and callers routinely pass the
  snapshot around (CLI → API → report) where repeated recompute would
  be wasteful. Keep :func:`opstree.fleet.compute_variance` pure and let
  :func:`scan_fleet` call it once at construction time.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from opstree.snapshot.model import Snapshot


class FleetVariance(BaseModel):
    """Summary of fields that disagree across fleet members.

    ``fields`` maps a dotted layer-scoped path (e.g.
    ``"physical.display.data.resolution"``) to the per-target value
    observed at that path. Only paths whose value is NOT identical
    across every target are recorded — if the whole fleet agrees,
    the path is absent.

    A missing value (target didn't report that field at all) is stored
    as ``None`` and still counts as a divergence.
    """

    model_config = {"frozen": True}

    fields: dict[str, dict[str, Any]] = Field(default_factory=dict)
    by_layer: dict[str, int] = Field(default_factory=dict)

    @property
    def is_uniform(self) -> bool:
        """True iff every observed field is identical across the fleet."""
        return not self.fields

    @property
    def diverging_paths(self) -> list[str]:
        """Sorted list of paths that vary across the fleet."""
        return sorted(self.fields.keys())


class FleetSnapshot(BaseModel):
    """N :class:`Snapshot` instances plus their cross-host variance.

    Invariants:
    * ``set(snapshots) == set(targets)`` — every target has a snapshot.
    * ``targets`` preserves the caller's ordering (useful for reports);
      ``snapshots`` is a dict for O(1) lookup.
    """

    model_config = {"frozen": True}

    targets: list[str]
    snapshots: dict[str, Snapshot]
    variance: FleetVariance

    @property
    def size(self) -> int:
        """Number of successfully-scanned targets."""
        return len(self.snapshots)

    def for_target(self, target: str) -> Snapshot | None:
        """Return the snapshot for *target* or ``None`` if not scanned."""
        return self.snapshots.get(target)
