"""op3 drift command."""
from __future__ import annotations
import click
from pathlib import Path
from opstree.formats.less import LessAdapter
from opstree.snapshot.model import Snapshot
from opstree.drift.detector import DriftDetector


@click.command()
@click.argument("intended", type=click.Path(exists=True))
@click.argument("actual", type=click.Path(exists=True))
def drift(intended: str, actual: str):
    """Detect drift between intended and actual state."""
    intended_path = Path(intended)
    actual_path = Path(actual)

    if intended_path.suffix == ".less":
        adapter = LessAdapter()
        intended_partial = adapter.parse(intended_path.read_text())
    else:
        intended_partial = Snapshot.load(intended_path)

    actual_snapshot = Snapshot.load(actual_path)

    detector = DriftDetector()
    report = detector.detect(intended_partial, actual_snapshot)

    click.echo(f"Drift Report: {report.intended_source} → {report.actual_target}")
    click.echo(f"Has drift: {report.has_drift}")
    click.echo(f"Total changes: {report.summary.get('total_changes', 0)}")

    if report.has_drift:
        click.echo("\nChanges by type:")
        for change_type, count in report.summary.get("by_type", {}).items():
            click.echo(f"  {change_type}: {count}")

        click.echo("\nChanges by layer:")
        for layer_id, count in report.summary.get("by_layer", {}).items():
            click.echo(f"  {layer_id}: {count}")
