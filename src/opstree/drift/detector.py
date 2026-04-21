"""Drift detection between intended and actual state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from opstree.snapshot.model import Snapshot, PartialSnapshot
from opstree.snapshot.diff import snapshot_diff, Change


@dataclass
class DriftReport:
    """Report of drift between intended and actual state."""
    intended_source: str
    actual_target: str
    has_drift: bool
    changes: List[Change] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class DriftDetector:
    """Detect drift between intended state (from config) and actual state (from scan)."""
    
    def detect(
        self,
        intended: PartialSnapshot,
        actual: Snapshot,
    ) -> DriftReport:
        """Detect drift between intended and actual state.
        
        Args:
            intended: Partial snapshot from config file (LESS, migration.yaml, etc.)
            actual: Full snapshot from scanning the device
        
        Returns:
            DriftReport with changes and summary
        """
        # Convert PartialSnapshot to Snapshot for comparison
        intended_snapshot = Snapshot(
            target=intended.source_path or "unknown",
            scanned_at=actual.scanned_at,  # Use same timestamp for comparison
            scanner_version="0.1.5",
            layers=intended.layers,
        )
        
        changes = snapshot_diff(intended_snapshot, actual)
        
        has_drift = len(changes) > 0
        
        summary = self._summarize_changes(changes)
        
        return DriftReport(
            intended_source=intended.source_format,
            actual_target=actual.target,
            has_drift=has_drift,
            changes=changes,
            summary=summary,
        )
    
    def _summarize_changes(self, changes: List[Change]) -> Dict[str, Any]:
        """Summarize changes by type and layer."""
        summary = {
            "total_changes": len(changes),
            "by_type": {},
            "by_layer": {},
        }
        
        for change in changes:
            # Count by type
            if change.type not in summary["by_type"]:
                summary["by_type"][change.type] = 0
            summary["by_type"][change.type] += 1
            
            # Count by layer
            if change.layer_id not in summary["by_layer"]:
                summary["by_layer"][change.layer_id] = 0
            summary["by_layer"][change.layer_id] += 1
        
        return summary
