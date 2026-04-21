# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/op3
- **Primary Language**: python
- **Languages**: python: 39, shell: 1
- **Analysis Mode**: static
- **Total Functions**: 121
- **Total Classes**: 47
- **Modules**: 40
- **Entry Points**: 111

## Architecture by Module

### src.opstree.probes.builtin.physical_rpi
- **Functions**: 22
- **Classes**: 2
- **File**: `physical_rpi.py`

### src.opstree.probes.builtin.rpi_diagnostics
- **Functions**: 12
- **File**: `rpi_diagnostics.py`

### src.opstree.probes.builtin.os_linux
- **Functions**: 12
- **Classes**: 2
- **File**: `os_linux.py`

### src.opstree.probes.registry
- **Functions**: 7
- **Classes**: 1
- **File**: `registry.py`

### src.opstree.probes.builtin.runtime_container
- **Functions**: 6
- **Classes**: 1
- **File**: `runtime_container.py`

### src.opstree.diagnostics.rules
- **Functions**: 6
- **Classes**: 3
- **File**: `rules.py`

### src.opstree.layers.tree
- **Functions**: 6
- **Classes**: 2
- **File**: `tree.py`

### src.opstree.formats.registry
- **Functions**: 5
- **Classes**: 1
- **File**: `registry.py`

### src.opstree.probes.builtin.service_containers
- **Functions**: 5
- **Classes**: 1
- **File**: `service_containers.py`

### src.opstree.probes.builtin.business_health
- **Functions**: 5
- **Classes**: 1
- **File**: `business_health.py`

### src.opstree.probes.builtin.endpoint_http
- **Functions**: 5
- **Classes**: 1
- **File**: `endpoint_http.py`

### src.opstree.probes.context
- **Functions**: 4
- **Classes**: 5
- **File**: `context.py`

### src.opstree.probes.base
- **Functions**: 4
- **Classes**: 3
- **File**: `base.py`

### src.opstree.snapshot.model
- **Functions**: 4
- **Classes**: 3
- **File**: `model.py`

### src.opstree.formats.less
- **Functions**: 3
- **Classes**: 1
- **File**: `less.py`

### src.opstree.scanner.linear
- **Functions**: 3
- **Classes**: 1
- **File**: `linear.py`

### src.opstree.formats.migration_yaml
- **Functions**: 2
- **Classes**: 1
- **File**: `migration_yaml.py`

### src.opstree.formats.snapshot_yaml
- **Functions**: 2
- **Classes**: 1
- **File**: `snapshot_yaml.py`

### src.opstree.snapshot.diff
- **Functions**: 2
- **Classes**: 1
- **File**: `diff.py`

### src.opstree.drift.detector
- **Functions**: 2
- **Classes**: 2
- **File**: `detector.py`

## Key Entry Points

Main execution flows into the system:

### src.opstree.formats.less.LessAdapter.render
> Renderuj Snapshot → LESS.
- **Calls**: snapshot.layers.get, snapshot.layers.get, snapshot.layers.get, snapshot.layers.get, snapshot.layers.get, None.join, business_layer.data.get, business_layer.data.get

### src.opstree.formats.less.LessAdapter.parse
> Parsuj LESS → PartialSnapshot.
- **Calls**: re.search, re.finditer, re.finditer, re.finditer, re.search, PartialSnapshot, None.strip, None.strip

### src.opstree.cli.commands.scan.scan
> Scan a device and output snapshot.
- **Calls**: click.command, click.argument, click.option, click.option, click.option, click.option, LayerTree, ProbeRegistry

### src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe._list_containers
> Lista kontenerów.
- **Calls**: _exec, ctx.execute, hasattr, _exec, _exec, None.splitlines, len, json.loads

### src.opstree.cli.commands.convert.convert
> Convert between configuration formats.
- **Calls**: click.command, click.argument, click.argument, click.option, Path, None.write_text, click.echo, LessAdapter

### src.opstree.cli.commands.drift.drift
> Detect drift between intended and actual state.
- **Calls**: click.command, click.argument, click.argument, Path, Path, Snapshot.load, DriftDetector, detector.detect

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.scan
- **Calls**: self._probe_config_txt, self._extract_dsi_overlays, self._scan_drm, self._probe_wlr_randr, self._merge_wlr_into_drm, self._probe_dsi_dmesg, ProbeResult, self._probe_board_model

### src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.parse
> Parsuj snapshot.yaml → Snapshot.
- **Calls**: yaml.safe_load, None.items, Snapshot, LayerData, data.get, data.get, datetime.fromisoformat, data.get

### src.opstree.formats.migration_yaml.MigrationYamlAdapter.parse
> Parsuj migration.yaml → PartialSnapshot.
- **Calls**: yaml.safe_load, data.get, data.get, PartialSnapshot, LayerData, LayerData, LayerData, datetime.utcnow

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_wlr_randr
- **Calls**: _Exec.run, r.stdout.splitlines, results.append, r.stdout.strip, re.match, re.match, results.append, name_m.group

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_i2c_buses
- **Calls**: _Exec.run, r.lines, _Exec.run, re.search, int, buses.append, r.stdout.strip, m.group

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._scan_drm
- **Calls**: _Exec.run, listing.lines, re.match, m.group, _Exec.run, _Exec.run, _Exec.run, _Exec.run

### src.opstree.formats.migration_yaml.MigrationYamlAdapter.render
> Renderuj Snapshot → migration.yaml.
- **Calls**: snapshot.layers.get, snapshot.layers.get, snapshot.layers.get, yaml.dump, endpoint_layer.data.get, business_layer.data.get, ep.get, runtime_layer.data.get

### src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe._detect_runtime
> Wykryj runtime i wersję.
- **Calls**: ctx.execute, hasattr, _exec, _exec, _exec, None.strip, None.strip, None.split

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._scan_backlights
- **Calls**: _Exec.run, listing.lines, None.int_, None.int_, None.int_, out.append, listing.stdout.strip, None.text

### src.opstree.probes.builtin.os_linux.OsKernelProbe._get_uptime
- **Calls**: ctx.execute, hasattr, float, int, float, int, None.split, None.split

### src.opstree.diagnostics.rules.Rule.evaluate
> Return zero or more diagnostics produced by this rule.
- **Calls**: list, self.predicate, callable, self.message, callable, self.fix, self.evidence, Diagnostic

### src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.render
> Renderuj Snapshot → snapshot.yaml.
- **Calls**: snapshot.layers.items, hasattr, yaml.dump, hasattr, snapshot.scanned_at.isoformat, None.isoformat, hasattr, layer_data.probed_at.isoformat

### src.opstree.scanner.linear.LinearScanner.scan
> Scan all layers and return a complete snapshot.
- **Calls**: ProbeContext, self.layer_tree.topological_order, Snapshot, self.probe_registry.get, probe.can_probe, datetime.now, probe.scan, probe.anomalies

### src.opstree.probes.builtin.service_containers.ServiceContainersProbe._list_systemd_services
> Lista systemd services.
- **Calls**: _exec, ctx.execute, hasattr, None.splitlines, line.split, stdout.strip, len, services.append

### src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe._check_endpoint
> Sprawdź pojedynczy endpoint.
- **Calls**: _exec, _exec, ctx.execute, hasattr, int, int, stdout.strip, float

### src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.anomalies
> Wykryj anomalie w endpointach.
- **Calls**: data.data.get, ep.get, anomalies.append, ep.get, anomalies.append, ep.get, ep.get, ep.get

### src.opstree.layers.tree.LayerTree.topological_order
> Zwróć warstwy w kolejności do skanowania (DAG).
- **Calls**: self._layers.values, queue.pop, result.append, self._layers.values, len, len, ValueError, in_degree.items

### src.opstree.probes.builtin.rpi_diagnostics._i2c_chip_missing_rules
- **Calls**: src.opstree.probes.builtin.rpi_diagnostics._backlights, src.opstree.probes.builtin.rpi_diagnostics._backlight_chip_addr, next, bl.get, bus.get, Diagnostic, src.opstree.probes.builtin.rpi_diagnostics._i2c_buses, b.get

### src.opstree.formats.less.LessAdapter._parse_block
> Parse a LESS block into key-value pairs.
- **Calls**: body.split, line.strip, line.split, None.strip, line.startswith, key.strip, None.rstrip, value.strip

### src.opstree.probes.builtin.rpi_diagnostics._backlight_power_off_rules
- **Calls**: src.opstree.probes.builtin.rpi_diagnostics._backlights, bl.get, bl.get, bl.get, Diagnostic, Diagnostic, bl.get

### src.opstree.probes.builtin.physical_rpi._Exec.run
- **Calls**: ctx.execute, hasattr, cls, cls, cls, bool, getattr

### src.opstree.probes.builtin.os_linux.OsKernelProbe.scan
> Zeskanuj warstwę.
- **Calls**: ProbeResult, self._get_kernel_version, self._get_arch, self._get_hostname, self._get_uptime, LayerData, datetime.now

### src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.scan
> Zeskanuj warstwę.
- **Calls**: ProbeResult, endpoint.get, endpoint.get, self._check_endpoint, results.append, LayerData, datetime.now

### src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.can_probe
> Czy ten probe może pobiec w tym kontekście?
- **Calls**: ctx.execute, hasattr, _check, _check, _check, _check

## Process Flows

Key execution flows identified:

### Flow 1: render
```
render [src.opstree.formats.less.LessAdapter]
```

### Flow 2: parse
```
parse [src.opstree.formats.less.LessAdapter]
```

### Flow 3: scan
```
scan [src.opstree.cli.commands.scan]
```

### Flow 4: _list_containers
```
_list_containers [src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe]
```

### Flow 5: convert
```
convert [src.opstree.cli.commands.convert]
```

### Flow 6: drift
```
drift [src.opstree.cli.commands.drift]
```

### Flow 7: _probe_wlr_randr
```
_probe_wlr_randr [src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe]
```

### Flow 8: _probe_i2c_buses
```
_probe_i2c_buses [src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe]
```

### Flow 9: _scan_drm
```
_scan_drm [src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe]
```

### Flow 10: _detect_runtime
```
_detect_runtime [src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe]
```

## Key Classes

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe
> Full hardware probe for a Raspberry Pi-class board.
- **Methods**: 18
- **Key Methods**: src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.can_probe, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.scan, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.anomalies, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_board_model, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_config_txt, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._extract_dsi_overlays, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._scan_drm, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_wlr_randr, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._merge_wlr_into_drm, src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._scan_backlights

### src.opstree.probes.builtin.os_linux.OsKernelProbe
> Skanuje jądro Linux.
- **Methods**: 7
- **Key Methods**: src.opstree.probes.builtin.os_linux.OsKernelProbe.can_probe, src.opstree.probes.builtin.os_linux.OsKernelProbe.scan, src.opstree.probes.builtin.os_linux.OsKernelProbe._get_kernel_version, src.opstree.probes.builtin.os_linux.OsKernelProbe._get_arch, src.opstree.probes.builtin.os_linux.OsKernelProbe._get_hostname, src.opstree.probes.builtin.os_linux.OsKernelProbe._get_uptime, src.opstree.probes.builtin.os_linux.OsKernelProbe.anomalies

### src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe
> Skanuje runtime kontenerów (docker/podman).
- **Methods**: 6
- **Key Methods**: src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.__init__, src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.can_probe, src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.scan, src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe._detect_runtime, src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe._list_containers, src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.anomalies

### src.opstree.probes.builtin.service_containers.ServiceContainersProbe
> Skanuje systemd services.
- **Methods**: 5
- **Key Methods**: src.opstree.probes.builtin.service_containers.ServiceContainersProbe.can_probe, src.opstree.probes.builtin.service_containers.ServiceContainersProbe.scan, src.opstree.probes.builtin.service_containers.ServiceContainersProbe._list_systemd_services, src.opstree.probes.builtin.service_containers.ServiceContainersProbe._is_service_enabled, src.opstree.probes.builtin.service_containers.ServiceContainersProbe.anomalies

### src.opstree.probes.builtin.business_health.BusinessHealthProbe
> Skanuje zdrowie aplikacji.
- **Methods**: 5
- **Key Methods**: src.opstree.probes.builtin.business_health.BusinessHealthProbe.__init__, src.opstree.probes.builtin.business_health.BusinessHealthProbe.can_probe, src.opstree.probes.builtin.business_health.BusinessHealthProbe.scan, src.opstree.probes.builtin.business_health.BusinessHealthProbe._check_health_endpoint, src.opstree.probes.builtin.business_health.BusinessHealthProbe.anomalies

### src.opstree.probes.registry.ProbeRegistry
> Registry for probes keyed by ``layer_id``.

Each instance owns its own probe dict — create a fresh r
- **Methods**: 5
- **Key Methods**: src.opstree.probes.registry.ProbeRegistry.__init__, src.opstree.probes.registry.ProbeRegistry.register, src.opstree.probes.registry.ProbeRegistry.get, src.opstree.probes.registry.ProbeRegistry.all, src.opstree.probes.registry.ProbeRegistry.clear

### src.opstree.probes.builtin.os_linux.OsConfigProbe
> Skanuje konfigurację systemu.
- **Methods**: 5
- **Key Methods**: src.opstree.probes.builtin.os_linux.OsConfigProbe.can_probe, src.opstree.probes.builtin.os_linux.OsConfigProbe.scan, src.opstree.probes.builtin.os_linux.OsConfigProbe._read_config_txt, src.opstree.probes.builtin.os_linux.OsConfigProbe._read_cmdline, src.opstree.probes.builtin.os_linux.OsConfigProbe.anomalies

### src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe
> Skanuje HTTP endpoints.
- **Methods**: 5
- **Key Methods**: src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.__init__, src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.can_probe, src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.scan, src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe._check_endpoint, src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.anomalies

### src.opstree.layers.tree.LayerTree
> Drzewo warstw — topological ordering, dependency resolution.
- **Methods**: 5
- **Key Methods**: src.opstree.layers.tree.LayerTree.__init__, src.opstree.layers.tree.LayerTree.register, src.opstree.layers.tree.LayerTree.get, src.opstree.layers.tree.LayerTree.topological_order, src.opstree.layers.tree.LayerTree.to_fraq_node

### src.opstree.formats.registry.FormatRegistry
> Registry for format adapters (wraps fraq's FormatRegistry).
- **Methods**: 4
- **Key Methods**: src.opstree.formats.registry.FormatRegistry.register, src.opstree.formats.registry.FormatRegistry.get, src.opstree.formats.registry.FormatRegistry.available, src.opstree.formats.registry.FormatRegistry.serialize

### src.opstree.probes.builtin.physical_rpi._Exec
> Uniform adapter over the two shapes ``ProbeContext.execute`` returns.

Historically some probes retu
- **Methods**: 4
- **Key Methods**: src.opstree.probes.builtin.physical_rpi._Exec.run, src.opstree.probes.builtin.physical_rpi._Exec.lines, src.opstree.probes.builtin.physical_rpi._Exec.text, src.opstree.probes.builtin.physical_rpi._Exec.int_

### src.opstree.diagnostics.rules.RuleEngine
> Runs a list of :class:`Rule` objects against a subject.

Stateless and reusable; keep one per rule-s
- **Methods**: 4
- **Key Methods**: src.opstree.diagnostics.rules.RuleEngine.__init__, src.opstree.diagnostics.rules.RuleEngine.rules, src.opstree.diagnostics.rules.RuleEngine.evaluate, src.opstree.diagnostics.rules.RuleEngine.any_error
- **Inherits**: <ast.Subscript object at 0x705c70c29010>

### src.opstree.snapshot.model.Snapshot
> Pełna migawka urządzenia/systemu.
- **Methods**: 4
- **Key Methods**: src.opstree.snapshot.model.Snapshot.layer, src.opstree.snapshot.model.Snapshot.query, src.opstree.snapshot.model.Snapshot.to_yaml, src.opstree.snapshot.model.Snapshot.load
- **Inherits**: BaseModel

### src.opstree.formats.less.LessAdapter
> Parsuj i emituj .doql.less.
- **Methods**: 3
- **Key Methods**: src.opstree.formats.less.LessAdapter.parse, src.opstree.formats.less.LessAdapter.render, src.opstree.formats.less.LessAdapter._parse_block

### src.opstree.probes.base.Probe
> Kontrakt probe'a.
- **Methods**: 3
- **Key Methods**: src.opstree.probes.base.Probe.can_probe, src.opstree.probes.base.Probe.scan, src.opstree.probes.base.Probe.anomalies
- **Inherits**: Protocol

### src.opstree.formats.migration_yaml.MigrationYamlAdapter
> Parsuj i emituj migration.yaml (redeploy-compatible).
- **Methods**: 2
- **Key Methods**: src.opstree.formats.migration_yaml.MigrationYamlAdapter.parse, src.opstree.formats.migration_yaml.MigrationYamlAdapter.render

### src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter
> Native op3 snapshot format adapter.
- **Methods**: 2
- **Key Methods**: src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.parse, src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.render

### src.opstree.scanner.linear.LinearScanner
> Simple scanner that processes layers in topological order.
- **Methods**: 2
- **Key Methods**: src.opstree.scanner.linear.LinearScanner.__init__, src.opstree.scanner.linear.LinearScanner.scan

### src.opstree.diagnostics.rules.Rule
> Declarative diagnostic rule over subject ``T``.

Exactly one of ``predicate`` (single-shot) or ``dyn
- **Methods**: 2
- **Key Methods**: src.opstree.diagnostics.rules.Rule.__post_init__, src.opstree.diagnostics.rules.Rule.evaluate
- **Inherits**: <ast.Subscript object at 0x705c70c1cd90>

### src.opstree.drift.detector.DriftDetector
> Detect drift between intended state (from config) and actual state (from scan).
- **Methods**: 2
- **Key Methods**: src.opstree.drift.detector.DriftDetector.detect, src.opstree.drift.detector.DriftDetector._summarize_changes

## Data Transformation Functions

Key functions that process and transform data:

### src.opstree.formats.migration_yaml.MigrationYamlAdapter.parse
> Parsuj migration.yaml → PartialSnapshot.
- **Output to**: yaml.safe_load, data.get, data.get, PartialSnapshot, LayerData

### src.opstree.formats.registry.FormatRegistry.serialize
> Serialize data using the specified format.
- **Output to**: cls._registry.serialize

### src.opstree.formats.registry.register_format
> Decorator to register a format adapter.
- **Output to**: FormatRegistry.register

### src.opstree.formats.less.LessAdapter.parse
> Parsuj LESS → PartialSnapshot.
- **Output to**: re.search, re.finditer, re.finditer, re.finditer, re.search

### src.opstree.formats.less.LessAdapter._parse_block
> Parse a LESS block into key-value pairs.
- **Output to**: body.split, line.strip, line.split, None.strip, line.startswith

### src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.parse
> Parsuj snapshot.yaml → Snapshot.
- **Output to**: yaml.safe_load, None.items, Snapshot, LayerData, data.get

### src.opstree.cli.commands.convert.convert
> Convert between configuration formats.
- **Output to**: click.command, click.argument, click.argument, click.option, Path

### src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe._probe_compositor_processes
- **Output to**: _Exec.run, r.stdout.strip, int, None.split, x.strip

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.opstree.formats.less.LessAdapter.render` - 38 calls
- `src.opstree.formats.less.LessAdapter.parse` - 37 calls
- `src.opstree.cli.commands.scan.scan` - 37 calls
- `src.opstree.cli.commands.convert.convert` - 26 calls
- `src.opstree.cli.commands.drift.drift` - 26 calls
- `src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.scan` - 21 calls
- `src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.parse` - 19 calls
- `src.opstree.formats.migration_yaml.MigrationYamlAdapter.parse` - 18 calls
- `src.opstree.formats.migration_yaml.MigrationYamlAdapter.render` - 13 calls
- `src.opstree.diagnostics.rules.Rule.evaluate` - 10 calls
- `src.opstree.snapshot.diff.snapshot_diff` - 10 calls
- `src.opstree.formats.snapshot_yaml.SnapshotYamlAdapter.render` - 9 calls
- `src.opstree.scanner.linear.LinearScanner.scan` - 9 calls
- `src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.anomalies` - 9 calls
- `src.opstree.layers.tree.LayerTree.topological_order` - 9 calls
- `src.opstree.probes.builtin.physical_rpi._Exec.run` - 7 calls
- `src.opstree.probes.builtin.os_linux.OsKernelProbe.scan` - 7 calls
- `src.opstree.probes.builtin.endpoint_http.EndpointHttpProbe.scan` - 7 calls
- `src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.can_probe` - 6 calls
- `src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.anomalies` - 6 calls
- `src.opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe.anomalies` - 6 calls
- `src.opstree.probes.builtin.business_health.BusinessHealthProbe.anomalies` - 6 calls
- `src.opstree.layers.tree.LayerDefinition.to_fraq_node` - 6 calls
- `src.opstree.probes.builtin.runtime_container.RuntimeContainerProbe.scan` - 5 calls
- `src.opstree.probes.builtin.os_linux.OsConfigProbe.scan` - 5 calls
- `src.opstree.drift.detector.DriftDetector.detect` - 5 calls
- `src.opstree.probes.builtin.service_containers.ServiceContainersProbe.scan` - 4 calls
- `src.opstree.probes.builtin.service_containers.ServiceContainersProbe.anomalies` - 4 calls
- `src.opstree.probes.builtin.business_health.BusinessHealthProbe.scan` - 4 calls
- `src.opstree.layers.tree.LayerTree.register` - 4 calls
- `src.opstree.snapshot.model.Snapshot.load` - 4 calls
- `src.opstree.layers.tree.LayerTree.to_fraq_node` - 3 calls
- `src.opstree.probes.builtin.rpi_diagnostics.diagnose_display_layer` - 2 calls
- `src.opstree.cli.main.cli` - 2 calls
- `src.opstree.probes.builtin.physical_rpi._Exec.lines` - 2 calls
- `src.opstree.probes.builtin.physical_rpi._Exec.int_` - 2 calls
- `src.opstree.scanner.linear.scan_device` - 2 calls
- `src.opstree.probes.builtin.service_containers.ServiceContainersProbe.can_probe` - 2 calls
- `src.opstree.probes.registry.ProbeRegistry.register` - 2 calls
- `src.opstree.probes.registry.ProbeRegistry.get` - 2 calls

## System Interactions

How components interact:

```mermaid
graph TD
    render --> get
    parse --> search
    parse --> finditer
    scan --> command
    scan --> argument
    scan --> option
    _list_containers --> _exec
    _list_containers --> execute
    _list_containers --> hasattr
    convert --> command
    convert --> argument
    convert --> option
    convert --> Path
    drift --> command
    drift --> argument
    drift --> Path
    scan --> _probe_config_txt
    scan --> _extract_dsi_overlay
    scan --> _scan_drm
    scan --> _probe_wlr_randr
    scan --> _merge_wlr_into_drm
    parse --> safe_load
    parse --> items
    parse --> Snapshot
    parse --> LayerData
    parse --> get
    parse --> PartialSnapshot
    _probe_wlr_randr --> run
    _probe_wlr_randr --> splitlines
    _probe_wlr_randr --> append
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.