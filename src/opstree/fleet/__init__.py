"""Fleet scanning — scan N targets together, compute cross-host variance.

``scan_fleet`` runs an existing :class:`LinearScanner` against multiple
targets concurrently and returns a :class:`FleetSnapshot` that bundles

* the per-target :class:`Snapshot` results, and
* a :class:`FleetVariance` describing every field whose value is not
  the same on every host.

This is the op3 primitive underneath downstream features such as
``doql adopt --from-fleet`` (derive a shared LESS from many devices)
and ``redeploy drift --fleet`` (check a whole tag cohort at once).
"""
from opstree.fleet.model import FleetSnapshot, FleetVariance
from opstree.fleet.scanner import compute_variance, scan_fleet
from opstree.fleet.formats import render_common_as_snapshot, render_variant_matrix

__all__ = [
    "FleetSnapshot",
    "FleetVariance",
    "compute_variance",
    "scan_fleet",
    "render_common_as_snapshot",
    "render_variant_matrix",
]
