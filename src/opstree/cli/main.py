"""CLI for op3 — operations tree scanning and drift detection."""
from __future__ import annotations
import click
from pathlib import Path
from opstree.layers.tree import LayerTree
from opstree.layers.builtin import (
    PhysicalLayer, OsLayer, RuntimeLayer,
    ServiceLayer, EndpointLayer, BusinessLayer,
)
from opstree.probes.context import SSHContext, LocalContext
from opstree.probes.builtin.physical_rpi import RpiPhysicalDisplayProbe
from opstree.probes.builtin.os_linux import OsKernelProbe, OsConfigProbe
from opstree.probes.builtin.runtime_container import RuntimeContainerProbe
from opstree.scanner.linear import scan_device
from opstree.formats.less import LessAdapter
from opstree.formats.migration_yaml import MigrationYamlAdapter
from opstree.formats.snapshot_yaml import SnapshotYamlAdapter
from opstree.snapshot.model import Snapshot


@click.group()
@click.version_option(version="0.1.4")
def cli():
    """op3 — Layered operations tree for infrastructure observation."""
    pass


@cli.command()
@click.argument("target", default="localhost")
@click.option("--layers", "-l", help="Comma-separated list of layers to scan")
@click.option("--ssh", is_flag=True, help="Use SSH context (default: local)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")
def scan(target: str, ssh: bool, output: str, format: str, layers: str):
    """Scan a device and output snapshot."""
    # Setup layer tree with builtin layers
    # Filter layers if specified
    if layers:
        layer_filter = set(l.strip() for l in layers.split(","))
    else:
        layer_filter = None
    tree = LayerTree()
    if layer_filter is None or "physical.display" in layer_filter:
            tree.register(PhysicalLayer.display)
    if layer_filter is None or "physical.compute" in layer_filter:
            tree.register(PhysicalLayer.compute)
    if layer_filter is None or "os.kernel" in layer_filter:
            tree.register(OsLayer.kernel)
    if layer_filter is None or "os.config" in layer_filter:
            tree.register(OsLayer.config)
    if layer_filter is None or "runtime.container" in layer_filter:
            tree.register(RuntimeLayer.container)
    
    # Setup probes
    from opstree.probes.registry import ProbeRegistry
    registry = ProbeRegistry()
    registry.register(RpiPhysicalDisplayProbe())
    registry.register(OsKernelProbe())
    registry.register(OsConfigProbe())
    registry.register(RuntimeContainerProbe())
    
    # Setup context
    if ssh:
        ctx = SSHContext(target=target)
    else:
        ctx = LocalContext()
    
    # Scan
    scanner = type('Scanner', (), {'layer_tree': tree, 'probe_registry': registry})()
    snapshot = scan_device(target, ctx.execute, tree)
    
    # Fix scanner to use registry
    from opstree.scanner.linear import LinearScanner
    scanner = LinearScanner(tree)
    scanner.probe_registry = registry
    snapshot = scanner.scan(target, ctx.execute)
    
    # Output
    if format == "yaml":
        output_text = snapshot.to_yaml()
    else:
        import json
        output_text = json.dumps(snapshot.model_dump(mode="json"), indent=2)
    
    if output:
        Path(output).write_text(output_text)
        click.echo(f"Snapshot written to {output}")
    else:
        click.echo(output_text)


@cli.command()
@click.argument("intended", type=click.Path(exists=True))
@click.argument("actual", type=click.Path(exists=True))
def drift(intended: str, actual: str):
    """Detect drift between intended and actual state."""
    from opstree.snapshot.model import Snapshot, PartialSnapshot
    from opstree.drift.detector import DriftDetector
    
    # Load files
    intended_path = Path(intended)
    actual_path = Path(actual)
    
    if intended_path.suffix == ".less":
        adapter = LessAdapter()
        intended_partial = adapter.parse(intended_path.read_text())
    else:
        intended_partial = Snapshot.load(intended_path)
    
    actual_snapshot = Snapshot.load(actual_path)
    
    # Detect drift
    detector = DriftDetector()
    report = detector.detect(intended_partial, actual_snapshot)
    
    # Output report
    click.echo(f"Drift Report: {report.intended_source} → {report.actual_target}")
    click.echo(f"Has drift: {report.has_drift}")
    click.echo(f"Total changes: {report.summary.get('total_changes', 0)}")
    
    if report.has_drift:
        click.echo("\nChanges by type:")
        for change_type, count in report.summary.get('by_type', {}).items():
            click.echo(f"  {change_type}: {count}")
        
        click.echo("\nChanges by layer:")
        for layer_id, count in report.summary.get('by_layer', {}).items():
            click.echo(f"  {layer_id}: {count}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("--format", "-f", type=click.Choice(["less", "migration_yaml", "snapshot_yaml"]), required=True, help="Target format")
def convert(input_file: str, output_file: str, format: str):
    """Convert between configuration formats."""
    from datetime import datetime, timezone
    input_path = Path(input_file)
    
    # Load input
    if input_path.suffix == ".less":
        adapter = LessAdapter()
        partial = adapter.parse(input_path.read_text())
    elif input_path.name == "migration.yaml" or input_path.suffix == ".migration.yaml":
        adapter = MigrationYamlAdapter()
        partial = adapter.parse(input_path.read_text())
    else:
        snapshot = Snapshot.load(input_path)
    
    # Convert PartialSnapshot to Snapshot for snapshot_yaml output
    if input_path.suffix == ".less" or (input_path.name == "migration.yaml" or input_path.suffix == ".migration.yaml"):
        if format == "snapshot_yaml":
            snapshot = Snapshot(
                target="unknown",
                scanned_at=datetime.now(timezone.utc),
                scanner_version="0.1.4",
                layers=partial.layers,
                anomalies=[],
            )
        else:
            snapshot = partial
    
    # Convert to target format
    if format == "less":
        adapter = LessAdapter()
        output_text = adapter.render(snapshot)
    elif format == "migration_yaml":
        adapter = MigrationYamlAdapter()
        output_text = adapter.render(snapshot)
    elif format == "snapshot_yaml":
        adapter = SnapshotYamlAdapter()
        output_text = adapter.render(snapshot)
    
    # Write output
    Path(output_file).write_text(output_text)
    click.echo(f"Converted {input_file} → {output_file} ({format})")


if __name__ == "__main__":
    cli()
