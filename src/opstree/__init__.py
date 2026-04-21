"""op3 — operations tree for layered infrastructure observation."""

from opstree.layers.tree import LayerTree
from opstree.layers.builtin import (
    PhysicalLayer, OsLayer, RuntimeLayer, 
    ServiceLayer, EndpointLayer, BusinessLayer,
)
from opstree.snapshot.model import Snapshot, LayerData, PartialSnapshot
from opstree.snapshot.diff import snapshot_diff, Change
from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.probes.registry import ProbeRegistry, register_probe
from opstree.scanner.linear import LinearScanner, scan_device
from opstree.formats import FormatRegistry, register_format
from opstree.drift.detector import DriftDetector, DriftReport

__version__ = "0.1.7"

__all__ = [
    # Layers
    "LayerTree",
    "PhysicalLayer", "OsLayer", "RuntimeLayer",
    "ServiceLayer", "EndpointLayer", "BusinessLayer",
    # Snapshot
    "Snapshot", "LayerData", "PartialSnapshot",
    "snapshot_diff", "Change",
    # Probes
    "Probe", "ProbeContext", "ProbeResult",
    "ProbeRegistry", "register_probe",
    # Scanner
    "LinearScanner", "scan_device",
    # Formats
    "FormatRegistry", "register_format",
    # Drift
    "DriftDetector", "DriftReport",
]
