"""op3 convert command."""
from __future__ import annotations
import click
from pathlib import Path
from datetime import datetime, timezone
from opstree._version import __version__
from opstree.formats.less import LessAdapter
from opstree.formats.migration_yaml import MigrationYamlAdapter
from opstree.formats.snapshot_yaml import SnapshotYamlAdapter
from opstree.snapshot.model import Snapshot


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("--format", "-f", type=click.Choice(["less", "migration_yaml", "snapshot_yaml"]), required=True, help="Target format")
def convert(input_file: str, output_file: str, format: str):
    """Convert between configuration formats."""
    input_path = Path(input_file)

    if input_path.suffix == ".less":
        adapter = LessAdapter()
        partial = adapter.parse(input_path.read_text())
    elif input_path.name == "migration.yaml" or input_path.suffix == ".migration.yaml":
        adapter = MigrationYamlAdapter()
        partial = adapter.parse(input_path.read_text())
    else:
        snapshot = Snapshot.load(input_path)

    if input_path.suffix == ".less" or (input_path.name == "migration.yaml" or input_path.suffix == ".migration.yaml"):
        if format == "snapshot_yaml":
            snapshot = Snapshot(
                target="unknown",
                scanned_at=datetime.now(timezone.utc),
                scanner_version=__version__,
                layers=partial.layers,
                anomalies=[],
            )
        else:
            snapshot = partial

    if format == "less":
        adapter = LessAdapter()
        output_text = adapter.render(snapshot)
    elif format == "migration_yaml":
        adapter = MigrationYamlAdapter()
        output_text = adapter.render(snapshot)
    elif format == "snapshot_yaml":
        adapter = SnapshotYamlAdapter()
        output_text = adapter.render(snapshot)

    Path(output_file).write_text(output_text)
    click.echo(f"Converted {input_file} → {output_file} ({format})")
