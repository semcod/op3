"""Concurrent fleet scanner + variance computation.

The heavy lifting of per-host scanning already lives in
:class:`opstree.scanner.LinearScanner`. This module adds two things:

1. :func:`scan_fleet` — run that scanner against N targets in parallel
   using a :class:`concurrent.futures.ThreadPoolExecutor`. Threads are
   appropriate here because individual scans are I/O-bound (SSH round
   trips, subprocess calls) rather than CPU-bound.

2. :func:`compute_variance` — deterministic, pure function that
   flattens each snapshot's layer data and records every path whose
   value is not identical across the whole fleet.

The caller is responsible for building a wired ``LinearScanner`` (via
:func:`opstree.build_scanner`) and for producing the per-target
``execute`` callable (e.g. by instantiating
:class:`opstree.probes.context.SSHContext` with each target). This
keeps fleet scanning transport-agnostic.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Mapping

from opstree.fleet.model import FleetSnapshot, FleetVariance
from opstree.scanner.linear import LinearScanner
from opstree.snapshot.model import Snapshot


ExecuteFn = Callable[[str], Any]
"""A callable ``(cmd: str) -> ExecuteResult``.

Matches the signature of :attr:`opstree.ProbeContext.execute`.
"""


# ── variance ──────────────────────────────────────────────────────────────


_MISSING = object()


def _flatten(prefix: str, value: Any, out: dict[str, Any]) -> None:
    """Walk *value* recursively and emit leaf paths into *out*.

    Dicts are descended; lists and scalars are stored as-is. An empty
    dict is preserved as a leaf so that "layer present but empty" is
    distinguishable from "layer absent" in the variance output.
    """
    if isinstance(value, dict):
        if not value:
            out[prefix] = value
            return
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else str(k)
            _flatten(child, v, out)
    else:
        out[prefix] = value


def _flatten_snapshot(snap: Snapshot) -> dict[str, Any]:
    """Flatten a snapshot into ``{"<layer>.data.<...>": value}``.

    Only the ``data`` attribute of each ``LayerData`` is flattened —
    ``probed_at`` / ``probed_by`` / ``raw_evidence`` would otherwise
    drown real drift in noise (different timestamps, different
    probe identities are expected per-host).
    """
    flat: dict[str, Any] = {}
    for layer_id, layer_data in snap.layers.items():
        _flatten(f"{layer_id}.data", layer_data.data, flat)
    return flat


def _canonicalise(value: Any) -> Any:
    """Return a hashable representative of *value* for equality checks.

    Lists and dicts aren't hashable, so we round-trip through JSON with
    sorted keys to get a stable canonical form. Falls back to ``repr``
    for anything JSON can't serialise.
    """
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return repr(value)
    if value is _MISSING:
        return _MISSING
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


def _layer_of(path: str) -> str | None:
    """Derive the layer id (e.g. ``physical.display``) from a variance path."""
    # Paths look like "<type>.<instance>.data.<field>..." — the layer id
    # is the first two dotted segments.
    parts = path.split(".")
    if len(parts) < 2:
        return None
    return f"{parts[0]}.{parts[1]}"


def compute_variance(snapshots: Mapping[str, Snapshot]) -> FleetVariance:
    """Compute cross-host variance over a mapping of ``{target: Snapshot}``.

    A path is recorded iff at least two targets disagree on its value
    (including "one has it, another doesn't" — the absent side is
    stored as ``None``). Fewer than two snapshots trivially produces
    uniform variance.
    """
    if len(snapshots) < 2:
        return FleetVariance()

    flat_per_target: dict[str, dict[str, Any]] = {
        tgt: _flatten_snapshot(snap) for tgt, snap in snapshots.items()
    }

    all_paths: set[str] = set()
    for flat in flat_per_target.values():
        all_paths.update(flat.keys())

    fields: dict[str, dict[str, Any]] = {}
    by_layer: dict[str, int] = {}

    for path in sorted(all_paths):
        per_target = {
            tgt: flat.get(path, _MISSING) for tgt, flat in flat_per_target.items()
        }
        unique = {_canonicalise(v) for v in per_target.values()}
        if len(unique) <= 1:
            continue

        fields[path] = {
            tgt: (None if v is _MISSING else v) for tgt, v in per_target.items()
        }
        layer = _layer_of(path)
        if layer is not None:
            by_layer[layer] = by_layer.get(layer, 0) + 1

    return FleetVariance(fields=fields, by_layer=by_layer)


# ── scan ──────────────────────────────────────────────────────────────────


def scan_fleet(
    scanner: LinearScanner,
    target_execute: Mapping[str, ExecuteFn],
    *,
    max_workers: int | None = None,
) -> FleetSnapshot:
    """Scan every target in ``target_execute`` concurrently.

    Parameters
    ----------
    scanner:
        A wired :class:`LinearScanner` (typically from
        :func:`opstree.build_scanner`). The scanner's layer tree and
        probe registry are read-only during a scan, so a single scanner
        instance is safe to reuse across threads.
    target_execute:
        Mapping ``{target: execute_fn}``. The target string becomes the
        snapshot's ``target`` field; ``execute_fn`` is the callable the
        probes use to run commands on that target.
    max_workers:
        Thread-pool size. Defaults to ``min(32, len(target_execute))``
        which matches the stdlib default behaviour for I/O-bound work
        while capping blow-up on very large fleets.

    Returns
    -------
    FleetSnapshot
        With ``targets`` preserving the iteration order of
        ``target_execute``, ``snapshots`` only containing successfully
        scanned targets, and ``variance`` computed across the successful
        snapshots.

    Notes
    -----
    Per-target failures currently bubble up as exceptions; we don't yet
    have a policy for "partial fleet scan" (skip, retry, fail-fast).
    When we add one it will take an explicit ``on_error`` parameter so
    the default behaviour stays predictable.
    """
    targets = list(target_execute.keys())

    if not targets:
        return FleetSnapshot(targets=[], snapshots={}, variance=FleetVariance())

    workers = max_workers if max_workers is not None else min(32, len(targets))
    snapshots: dict[str, Snapshot] = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_target = {
            pool.submit(scanner.scan, target, target_execute[target]): target
            for target in targets
        }
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            snapshots[target] = future.result()

    variance = compute_variance(snapshots)

    return FleetSnapshot(
        targets=targets,
        snapshots=snapshots,
        variance=variance,
    )


__all__ = [
    "ExecuteFn",
    "compute_variance",
    "scan_fleet",
]
