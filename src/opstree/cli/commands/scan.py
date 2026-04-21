"""op3 scan command."""
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
from opstree.scanner.linear import scan_device, LinearScanner
from opstree.snapshot.model import Snapshot


@click.command()
@click.argument("target", default="localhost")
@click.option("--layers", "-l", help="Comma-separated list of layers to scan")
@click.option("--ssh", is_flag=True, help="Use SSH context (default: local)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")
def scan(target: str, ssh: bool, output: str, format: str, layers: str):
    """Scan a device and output snapshot."""
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

    from opstree.probes.registry import ProbeRegistry
    registry = ProbeRegistry()
    registry.register(RpiPhysicalDisplayProbe())
    registry.register(OsKernelProbe())
    registry.register(OsConfigProbe())
    registry.register(RuntimeContainerProbe())

    if ssh:
        ctx = SSHContext(target=target)
    else:
        ctx = LocalContext()

    scanner = LinearScanner(tree)
    scanner.probe_registry = registry
    snapshot = scanner.scan(target, ctx.execute)

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
