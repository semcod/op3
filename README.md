# op3 — Layered Operations Tree


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.5-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$2.40-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-5.6h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $2.4000 (16 commits)
- 👤 **Human dev:** ~$556 (5.6h @ $100/h, 30min dedup)

Generated on 2026-04-21 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Layered infrastructure observation: observe, diff, orchestrate infrastructure as data.

## Overview

op3 provides a unified framework for observing hierarchical infrastructure state across multiple layers:

- **Physical Layer**: Hardware, displays, network, compute
- **OS Layer**: Kernel, configuration
- **Runtime Layer**: Containers, compositor
- **Service Layer**: Containers, systemd services
- **Endpoint Layer**: HTTP endpoints, TCP ports
- **Business Layer**: Application health, business logic

Built on fraq's fractal data primitives, op3 enables:
- Deterministic layer scanning with probe system
- Format adapters (LESS, migration.yaml, snapshot.yaml)
- Drift detection between intended and actual state
- Immutable snapshots with diff capabilities

## Installation

```bash
pip install op3
```

## Quick Start

```python
from opstree import LayerTree, LinearScanner, scan_device
from opstree.layers.builtin import PhysicalLayer, OsLayer, RuntimeLayer

# Register layers
tree = LayerTree()
tree.register(PhysicalLayer.display)
tree.register(OsLayer.kernel)
tree.register(RuntimeLayer.container)

# Scan a device
def execute(cmd: str):
    # Your SSH/local execution logic
    stdout, stderr, rc = ...
    return stdout, stderr, rc

snapshot = scan_device("pi@192.168.188.109", execute, tree)
print(snapshot.to_yaml())
```

## Format Adapters

```python
from opstree.formats.less import LessAdapter

adapter = LessAdapter()

# Parse LESS to PartialSnapshot
partial = adapter.parse(open("app.doql.less").read())

# Render Snapshot to LESS
less_output = adapter.render(snapshot)
```

## Project Status

**Sprint 4 Complete** (2026-04-21)
- ✅ Fixed datetime deprecation warnings (datetime.utcnow() → datetime.now(timezone.utc))
- ✅ All 26 tests passing with zero warnings

**Sprint 5 Complete** (2026-04-21)
- ✅ Added business.health builtin probe
- ✅ Added CLI layer filtering option (--layers flag)

**Sprint 6 Complete** (2026-04-21)
- ✅ Tested op3 with real-world examples from fraq, redeploy, doql
- ✅ Created examples/ folder with app.doql.less files from all three projects
- ✅ Enhanced CLI convert command to handle migration.yaml format
- ✅ All 26 tests passing

**Sprint 3 Complete** (2026-04-21)
- ✅ CLI with scan, drift, and convert commands
- ✅ Builtin probes (service.containers, endpoint.http)
- ✅ Format conversion between LESS, migration.yaml, snapshot.yaml
- ✅ CLI integration tested

**Sprint 2 Complete** (2026-04-21)
- ✅ Probe contexts (SSH, Local, Mock)
- ✅ Builtin probes (RPi display, Linux OS, container runtime)
- ✅ Format adapters (migration.yaml, snapshot.yaml)
- ✅ Integration tests with mock context (2 passing)
- ✅ ExecuteResult handling for compatibility

**Sprint 1 Complete** (2026-04-21)
- ✅ Layer tree with topological ordering
- ✅ Builtin layer definitions
- ✅ Snapshot model with Pydantic
- ✅ Probe protocol and registry
- ✅ Linear scanner
- ✅ Format registry (wraps fraq)
- ✅ LESS format adapter
- ✅ Unit tests (16 passing)

## Dependencies

- fraq >= 0.2.15 (core primitives: FraqNode, FormatRegistry, adapters)
- pydantic >= 2.0
- pyyaml >= 6.0
- click >= 8.0
- jmespath >= 1.0
- rich >= 13.0

## License

Licensed under Apache-2.0.
