<!-- code2docs:start --># op3

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-86-green)
> **86** functions | **43** classes | **34** files | CC̄ = 3.7

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/op3](https://github.com/semcod/op3)

## Installation

### From PyPI

```bash
pip install op3
```

### From Source

```bash
git clone https://github.com/semcod/op3
cd op3
pip install -e .
```

### Optional Extras

```bash
pip install op3[ssh]    # ssh features
pip install op3[async]    # async features
pip install op3[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
op3 ./my-project

# Only regenerate README
op3 ./my-project --readme-only

# Preview what would be generated (no file writes)
op3 ./my-project --dry-run

# Check documentation health
op3 check ./my-project

# Sync — regenerate only changed modules
op3 sync ./my-project
```

### Python API

```python
from op3 import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
op3/
├── project
            ├── builtin/
            ├── less
            ├── registry
        ├── formats/
            ├── snapshot_yaml
        ├── config_apply/
        ├── cli/
    ├── opstree/
                ├── endpoint_http
            ├── commands/
        ├── _version
        ├── scanner/
        ├── layers/
            ├── linear
        ├── snapshot/
                ├── business_health
                ├── os_linux
    ├── op3/
                ├── service_containers
            ├── main
                ├── runtime_container
            ├── registry
        ├── drift/
            ├── migration_yaml
        ├── probes/
                ├── physical_rpi
            ├── context
            ├── base
            ├── detector
            ├── diff
            ├── tree
            ├── model
            ├── builtin
```

## API Overview

### Classes

- **`LessAdapter`** — Parsuj i emituj .doql.less.
- **`FormatRegistry`** — Registry for format adapters (wraps fraq's FormatRegistry).
- **`SnapshotYamlAdapter`** — Native op3 snapshot format adapter.
- **`EndpointHttpProbe`** — Skanuje HTTP endpoints.
- **`LinearScanner`** — Simple scanner that processes layers in topological order.
- **`BusinessHealthProbe`** — Skanuje zdrowie aplikacji.
- **`OsKernelProbe`** — Skanuje jądro Linux.
- **`OsConfigProbe`** — Skanuje konfigurację systemu.
- **`ServiceContainersProbe`** — Skanuje systemd services.
- **`RuntimeContainerProbe`** — Skanuje runtime kontenerów (docker/podman).
- **`ProbeRegistry`** — Registry for probes by layer_id.
- **`MigrationYamlAdapter`** — Parsuj i emituj migration.yaml (redeploy-compatible).
- **`RpiPhysicalDisplayProbe`** — Skanuje DSI/HDMI/backlight na Raspberry Pi.
- **`ExecuteResult`** — Result of command execution.
- **`ProbeContext`** — Base context for probe execution.
- **`LocalContext`** — Local execution context (runs commands on localhost).
- **`MockContext`** — Mock context for testing with predefined responses.
- **`SSHContext`** — SSH execution context for remote scanning.
- **`ProbeContext`** — Kontekst dla probe — nie wie o SSH, click, nic konkretnego.
- **`ProbeResult`** — Wynik probe'a.
- **`Probe`** — Kontrakt probe'a.
- **`DriftReport`** — Report of drift between intended and actual state.
- **`DriftDetector`** — Detect drift between intended state (from config) and actual state (from scan).
- **`Change`** — Represents a single change between two snapshots.
- **`LayerDefinition`** — Definicja jednej warstwy w drzewie.
- **`LayerTree`** — Drzewo warstw — topological ordering, dependency resolution.
- **`LayerData`** — Dane jednej warstwy.
- **`Snapshot`** — Pełna migawka urządzenia/systemu.
- **`PartialSnapshot`** — Niepełna migawka — np. z parsowania LESS-a gdzie nie ma wszystkich warstw.
- **`PhysicalDisplayData`** — —
- **`OsKernelData`** — —
- **`OsConfigData`** — —
- **`RuntimeContainerData`** — —
- **`RuntimeCompositorData`** — —
- **`ServiceContainersData`** — —
- **`EndpointHttpData`** — —
- **`BusinessHealthData`** — —
- **`PhysicalLayer`** — Physical infrastructure layer.
- **`OsLayer`** — Operating system layer.
- **`RuntimeLayer`** — Runtime environment layer.
- **`ServiceLayer`** — Services layer.
- **`EndpointLayer`** — Network endpoints layer.
- **`BusinessLayer`** — Business logic layer.

### Functions

- `register_format(name, adapter)` — Decorator to register a format adapter.
- `scan_device(target, execute, layer_tree)` — Convenience function to scan a device.
- `cli()` — op3 — Layered operations tree for infrastructure observation.
- `scan(target, ssh, output, format)` — Scan a device and output snapshot.
- `drift(intended, actual)` — Detect drift between intended and actual state.
- `convert(input_file, output_file, format)` — Convert between configuration formats.
- `register_probe(probe_class)` — Decorator to register a probe class.
- `snapshot_diff(a, b)` — Compare two snapshots and return a list of changes.


## Project Structure

📄 `project`
📦 `src.op3`
📦 `src.opstree`
📄 `src.opstree._version`
📦 `src.opstree.cli`
📦 `src.opstree.cli.commands`
📄 `src.opstree.cli.main` (4 functions)
📦 `src.opstree.config_apply`
📦 `src.opstree.drift`
📄 `src.opstree.drift.detector` (2 functions, 2 classes)
📦 `src.opstree.formats`
📄 `src.opstree.formats.less` (3 functions, 1 classes)
📄 `src.opstree.formats.migration_yaml` (2 functions, 1 classes)
📄 `src.opstree.formats.registry` (5 functions, 1 classes)
📄 `src.opstree.formats.snapshot_yaml` (2 functions, 1 classes)
📦 `src.opstree.layers`
📄 `src.opstree.layers.builtin` (14 classes)
📄 `src.opstree.layers.tree` (6 functions, 2 classes)
📦 `src.opstree.probes`
📄 `src.opstree.probes.base` (4 functions, 3 classes)
📦 `src.opstree.probes.builtin`
📄 `src.opstree.probes.builtin.business_health` (5 functions, 1 classes)
📄 `src.opstree.probes.builtin.endpoint_http` (5 functions, 1 classes)
📄 `src.opstree.probes.builtin.os_linux` (12 functions, 2 classes)
📄 `src.opstree.probes.builtin.physical_rpi` (8 functions, 1 classes)
📄 `src.opstree.probes.builtin.runtime_container` (6 functions, 1 classes)
📄 `src.opstree.probes.builtin.service_containers` (5 functions, 1 classes)
📄 `src.opstree.probes.context` (4 functions, 5 classes)
📄 `src.opstree.probes.registry` (4 functions, 1 classes)
📦 `src.opstree.scanner`
📄 `src.opstree.scanner.linear` (3 functions, 1 classes)
📦 `src.opstree.snapshot`
📄 `src.opstree.snapshot.diff` (2 functions, 1 classes)
📄 `src.opstree.snapshot.model` (4 functions, 3 classes)

## Requirements

- Python >= >=3.10
- fraq >=0.2.15- pydantic >=2.0- pyyaml >=6.0- click >=8.0- jmespath >=1.0- rich >=13.0

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/op3
cd op3

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->