<!-- code2docs:start --># op3

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-435-green)
> **435** functions | **50** classes | **70** files | CC̄ = 3.7

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
├── SUMR
├── goal
├── op3_poc
├── SUMD
├── sumd
├── pyproject
├── CHANGELOG
├── project
├── README
    ├── API
    ├── README
        ├── snapshot
        ├── snapshot
        ├── migration
        ├── snapshot
        ├── _version
    ├── opstree/
            ├── detector
        ├── drift/
        ├── diagnostics/
            ├── rules
            ├── base
            ├── registry
        ├── probes/
            ├── context
                ├── business_health
                ├── os_linux
                ├── runtime_container
                ├── endpoint_http
            ├── builtin/
                ├── service_containers
                ├── rpi_diagnostics
                ├── physical_rpi
            ├── migration_yaml
            ├── less
            ├── registry
        ├── formats/
            ├── snapshot_yaml
        ├── config_apply/
        ├── cli/
            ├── main
                ├── convert
                ├── drift
            ├── commands/
                ├── scan
        ├── scanner/
            ├── linear
        ├── fleet/
            ├── scanner
            ├── model
        ├── layers/
            ├── tree
            ├── builtin
        ├── snapshot/
            ├── diff
            ├── model
        ├── integrations/
            ├── compat
    ├── op3/
        ├── toon
    ├── integration-roadmap
    ├── prompt
        ├── toon
        ├── toon
        ├── toon
    ├── context
    ├── README
        ├── toon
    ├── calls
        ├── toon
```

## API Overview

### Classes

- **`DriftReport`** — Report of drift between intended and actual state.
- **`DriftDetector`** — Detect drift between intended state (from config) and actual state (from scan).
- **`Diagnostic`** — A single finding emitted by a rule.
- **`Rule`** — Declarative diagnostic rule over subject ``T``.
- **`RuleEngine`** — Runs a list of :class:`Rule` objects against a subject.
- **`ProbeContext`** — Kontekst dla probe — nie wie o SSH, click, nic konkretnego.
- **`ProbeResult`** — Wynik probe'a.
- **`Probe`** — Kontrakt probe'a.
- **`ProbeRegistry`** — Registry for probes keyed by ``layer_id``.
- **`ExecuteResult`** — Result of command execution.
- **`ProbeContext`** — Base context for probe execution.
- **`LocalContext`** — Local execution context (runs commands on localhost).
- **`MockContext`** — Mock context for testing with predefined responses.
- **`SSHContext`** — SSH execution context for remote scanning.
- **`BusinessHealthProbe`** — Skanuje zdrowie aplikacji.
- **`OsKernelProbe`** — Skanuje jądro Linux.
- **`OsConfigProbe`** — Skanuje konfigurację systemu.
- **`RuntimeContainerProbe`** — Skanuje runtime kontenerów (docker/podman).
- **`EndpointHttpProbe`** — Skanuje HTTP endpoints.
- **`ServiceContainersProbe`** — Skanuje systemd services.
- **`RpiPhysicalDisplayProbe`** — Full hardware probe for a Raspberry Pi-class board.
- **`MigrationYamlAdapter`** — Parsuj i emituj migration.yaml (redeploy-compatible).
- **`LessAdapter`** — Parsuj i emituj .doql.less.
- **`FormatRegistry`** — Registry for format adapters (wraps fraq's FormatRegistry).
- **`SnapshotYamlAdapter`** — Native op3 snapshot format adapter.
- **`LinearScanner`** — Simple scanner that processes layers in topological order.
- **`FleetVariance`** — Summary of fields that disagree across fleet members.
- **`FleetSnapshot`** — N :class:`Snapshot` instances plus their cross-host variance.
- **`LayerDefinition`** — Definicja jednej warstwy w drzewie.
- **`LayerTree`** — Drzewo warstw — topological ordering, dependency resolution.
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
- **`Change`** — Represents a single change between two snapshots.
- **`LayerData`** — Dane jednej warstwy.
- **`Snapshot`** — Pełna migawka urządzenia/systemu.
- **`PartialSnapshot`** — Niepełna migawka — np. z parsowania LESS-a gdzie nie ma wszystkich warstw.
- **`CompatHelpers`** — Bundle of callables produced by :func:`make_compat_helpers`.

### Functions

- `convert()` — —
- `drift()` — —
- `scan()` — —
- `cli()` — —
- `compute_variance()` — —
- `scan_fleet()` — —
- `register_format()` — —
- `make_compat_helpers()` — —
- `diagnose_display_layer()` — —
- `get_default_registry()` — —
- `register_probe()` — —
- `build_layer_tree()` — —
- `build_scanner()` — —
- `scan_device()` — —
- `snapshot_diff()` — —
- `layer_tree()` — —
- `runner()` — —
- `test_cli_help()` — —
- `test_cli_scan_help()` — —
- `test_cli_convert_help()` — —
- `test_cli_convert_less_to_snapshot_yaml()` — —
- `test_cli_convert_less_to_migration_yaml()` — —
- `test_cli_convert_less_to_less()` — —
- `test_full_scan_with_mock_context()` — —
- `test_rpi_probe_anomaly_detection()` — —
- `test_probe_emits_full_hardware_dict()` — —
- `test_probe_output_feeds_diagnostics_to_clean_system()` — —
- `test_probe_output_feeds_diagnostics_to_broken_system()` — —
- `test_placeholder()` — —
- `test_import()` — —
- `test_build_layer_tree_registers_requested_leaf()` — —
- `test_build_layer_tree_pulls_transitive_dependencies()` — —
- `test_build_layer_tree_orders_deps_before_dependents()` — —
- `test_build_layer_tree_rejects_unknown_layer()` — —
- `test_build_layer_tree_deduplicates_shared_dependencies()` — —
- `test_build_scanner_uses_isolated_registry()` — —
- `test_build_scanner_registry_not_shared_with_default()` — —
- `test_build_scanner_populates_probes_for_requested_layers()` — —
- `test_build_scanner_include_default_probes_false_leaves_registry_empty()` — —
- `test_build_scanner_extra_probes_are_appended()` — —
- `test_build_scanner_end_to_end_scan()` — —
- `test_build_scanner_does_not_leak_into_subsequent_calls()` — —
- `test_rule_requires_exactly_one_of_predicate_or_dynamic()` — —
- `test_predicate_rule_requires_message()` — —
- `test_predicate_rule_fires_and_returns_diagnostic()` — —
- `test_predicate_rule_does_not_fire_returns_empty()` — —
- `test_dynamic_rule_fans_out_multiple_diagnostics()` — —
- `test_static_message_and_fix_strings()` — —
- `test_rule_evidence_callable()` — —
- `test_engine_aggregates_all_rules()` — —
- `test_engine_any_error_detects_firing_error_rule()` — —
- `test_engine_any_error_respects_exclude()` — —
- `test_diagnostic_to_dict_is_plain()` — —
- `test_compute_variance_empty_returns_uniform()` — —
- `test_compute_variance_single_snapshot_is_uniform()` — —
- `test_compute_variance_identical_fleet_has_no_fields()` — —
- `test_compute_variance_records_single_field_divergence()` — —
- `test_compute_variance_counts_diverging_fields_per_layer()` — —
- `test_compute_variance_records_missing_layer_as_none()` — —
- `test_compute_variance_is_order_independent()` — —
- `test_compute_variance_handles_nested_dict_equality()` — —
- `test_scan_fleet_empty_returns_empty_fleet_snapshot()` — —
- `test_scan_fleet_scans_each_target()` — —
- `test_scan_fleet_preserves_iteration_order_in_targets()` — —
- `test_scan_fleet_detects_drifted_kernel()` — —
- `test_scan_fleet_uniform_when_all_hosts_identical()` — —
- `test_scan_fleet_propagates_scanner_failure()` — —
- `test_fleet_snapshot_for_target_lookup()` — —
- `test_less_adapter_parse()` — —
- `test_less_adapter_render()` — —
- `test_less_adapter_roundtrip()` — —
- `test_op3_available_true()` — —
- `test_op3_enabled_truthy_values()` — —
- `test_op3_enabled_falsy_values()` — —
- `test_op3_enabled_env_absent()` — —
- `test_should_use_op3()` — —
- `test_require_op3_passes_when_available()` — —
- `test_make_mock_context_round_trip()` — —
- `test_make_ssh_context_factory()` — —
- `test_make_scanner_uses_defaults()` — —
- `test_make_scanner_respects_override()` — —
- `test_compat_helpers_frozen()` — —
- `test_layer_tree_registration()` — —
- `test_layer_tree_duplicate_registration()` — —
- `test_layer_tree_topological_order()` — —
- `test_layer_tree_cycle_detection()` — —
- `test_builtin_layers_exist()` — —
- `test_builtin_layer_dependencies()` — —
- `test_registry_instances_are_isolated()` — —
- `test_register_appends_multiple_probes_for_same_layer()` — —
- `test_get_returns_empty_list_for_unknown_layer()` — —
- `test_get_returns_copy_so_mutation_doesnt_leak()` — —
- `test_all_returns_deep_copy()` — —
- `test_clear_empties_registry()` — —
- `test_get_default_registry_returns_module_singleton()` — —
- `test_register_probe_decorator_uses_default_registry()` — —
- `test_decorator_does_not_pollute_user_registries()` — —
- `test_healthy_system_emits_only_all_ok()` — —
- `test_no_dsi_overlay_fires_when_overlay_missing()` — —
- `test_display_auto_detect_conflict()` — —
- `test_dsi_overlay_no_drm_connector()` — —
- `test_dsi_no_edid_panel_missing()` — —
- `test_dsi_connector_not_connected()` — —
- `test_dsi_connected_no_backlight()` — —
- `test_dsi_backlight_init_failed_extracts_error_code()` — —
- `test_no_drm_kernel_driver()` — —
- `test_dsi_driver_not_loaded()` — —
- `test_i2c_arm_not_enabled()` — —
- `test_i2c_backlight_bus_empty()` — —
- `test_compositor_not_running()` — —
- `test_wayland_socket_missing()` — —
- `test_chromium_not_running_info_only()` — —
- `test_dpms_off()` — —
- `test_no_wayland_output()` — —
- `test_all_ok_no_wayland()` — —
- `test_backlight_power_off_dynamic_rule()` — —
- `test_backlight_brightness_zero_dynamic_rule()` — —
- `test_i2c_chip_missing_dynamic_rule()` — —
- `test_rule_names_are_unique()` — —
- `test_layer_data_creation()` — —
- `test_snapshot_creation()` — —
- `test_snapshot_layer_accessor()` — —
- `test_snapshot_yaml_roundtrip()` — —
- `test_snapshot_diff_added_layer()` — —
- `test_snapshot_diff_removed_layer()` — —
- `test_snapshot_diff_modified_data()` — —
- `execute()` — —
- `print()` — —
- `generate_readme()` — —
- `get_default_registry()` — Return the process-global default registry.
- `register_probe(probe_class)` — Decorator: instantiate ``probe_class`` and register it on the
- `diagnose_display_layer(layer_data)` — Run the full RPi display rule-set against a layer data dict.
- `register_format(name, adapter)` — Decorator to register a format adapter.
- `cli()` — op3 — Layered operations tree for infrastructure observation.
- `convert(input_file, output_file, format)` — Convert between configuration formats.
- `drift(intended, actual)` — Detect drift between intended and actual state.
- `scan(target, ssh, output, format)` — Scan a device and output snapshot.
- `scan_device(target, execute, layer_tree)` — Convenience function to scan a device.
- `compute_variance(snapshots)` — Compute cross-host variance over a mapping of ``{target: Snapshot}``.
- `scan_fleet(scanner, target_execute)` — Scan every target in ``target_execute`` concurrently.
- `snapshot_diff(a, b)` — Compare two snapshots and return a list of changes.
- `make_compat_helpers()` — Build a :class:`CompatHelpers` bundle for a downstream project.
- `scan()` — —
- `convert()` — —
- `compute_variance()` — —
- `scan_fleet()` — —
- `diagnose_display_layer()` — —
- `scan_device()` — —
- `drift()` — —
- `snapshot_diff()` — —
- `get_default_registry()` — —
- `register_probe()` — —
- `register_format()` — —
- `cli()` — —
- `make_compat_helpers()` — —
- `execute()` — —
- `print()` — —
- `generate_readme()` — —
- `build_layer_tree()` — —
- `build_scanner()` — —
- `layer_tree()` — —
- `runner()` — —
- `test_cli_help()` — —
- `test_cli_scan_help()` — —
- `test_cli_convert_help()` — —
- `test_cli_convert_less_to_snapshot_yaml()` — —
- `test_cli_convert_less_to_migration_yaml()` — —
- `test_cli_convert_less_to_less()` — —
- `test_full_scan_with_mock_context()` — —
- `test_rpi_probe_anomaly_detection()` — —
- `test_probe_emits_full_hardware_dict()` — —
- `test_probe_output_feeds_diagnostics_to_clean_system()` — —
- `test_probe_output_feeds_diagnostics_to_broken_system()` — —
- `test_placeholder()` — —
- `test_import()` — —
- `test_build_layer_tree_registers_requested_leaf()` — —
- `test_build_layer_tree_pulls_transitive_dependencies()` — —
- `test_build_layer_tree_orders_deps_before_dependents()` — —
- `test_build_layer_tree_rejects_unknown_layer()` — —
- `test_build_layer_tree_deduplicates_shared_dependencies()` — —
- `test_build_scanner_uses_isolated_registry()` — —
- `test_build_scanner_registry_not_shared_with_default()` — —
- `test_build_scanner_populates_probes_for_requested_layers()` — —
- `test_build_scanner_include_default_probes_false_leaves_registry_empty()` — —
- `test_build_scanner_extra_probes_are_appended()` — —
- `test_build_scanner_end_to_end_scan()` — —
- `test_build_scanner_does_not_leak_into_subsequent_calls()` — —
- `test_rule_requires_exactly_one_of_predicate_or_dynamic()` — —
- `test_predicate_rule_requires_message()` — —
- `test_predicate_rule_fires_and_returns_diagnostic()` — —
- `test_predicate_rule_does_not_fire_returns_empty()` — —
- `test_dynamic_rule_fans_out_multiple_diagnostics()` — —
- `test_static_message_and_fix_strings()` — —
- `test_rule_evidence_callable()` — —
- `test_engine_aggregates_all_rules()` — —
- `test_engine_any_error_detects_firing_error_rule()` — —
- `test_engine_any_error_respects_exclude()` — —
- `test_diagnostic_to_dict_is_plain()` — —
- `test_compute_variance_empty_returns_uniform()` — —
- `test_compute_variance_single_snapshot_is_uniform()` — —
- `test_compute_variance_identical_fleet_has_no_fields()` — —
- `test_compute_variance_records_single_field_divergence()` — —
- `test_compute_variance_counts_diverging_fields_per_layer()` — —
- `test_compute_variance_records_missing_layer_as_none()` — —
- `test_compute_variance_is_order_independent()` — —
- `test_compute_variance_handles_nested_dict_equality()` — —
- `test_scan_fleet_empty_returns_empty_fleet_snapshot()` — —
- `test_scan_fleet_scans_each_target()` — —
- `test_scan_fleet_preserves_iteration_order_in_targets()` — —
- `test_scan_fleet_detects_drifted_kernel()` — —
- `test_scan_fleet_uniform_when_all_hosts_identical()` — —
- `test_scan_fleet_propagates_scanner_failure()` — —
- `test_fleet_snapshot_for_target_lookup()` — —
- `test_less_adapter_parse()` — —
- `test_less_adapter_render()` — —
- `test_less_adapter_roundtrip()` — —
- `test_op3_available_true()` — —
- `test_op3_enabled_truthy_values()` — —
- `test_op3_enabled_falsy_values()` — —
- `test_op3_enabled_env_absent()` — —
- `test_should_use_op3()` — —
- `test_require_op3_passes_when_available()` — —
- `test_make_mock_context_round_trip()` — —
- `test_make_ssh_context_factory()` — —
- `test_make_scanner_uses_defaults()` — —
- `test_make_scanner_respects_override()` — —
- `test_compat_helpers_frozen()` — —
- `test_layer_tree_registration()` — —
- `test_layer_tree_duplicate_registration()` — —
- `test_layer_tree_topological_order()` — —
- `test_layer_tree_cycle_detection()` — —
- `test_builtin_layers_exist()` — —
- `test_builtin_layer_dependencies()` — —
- `test_registry_instances_are_isolated()` — —
- `test_register_appends_multiple_probes_for_same_layer()` — —
- `test_get_returns_empty_list_for_unknown_layer()` — —
- `test_get_returns_copy_so_mutation_doesnt_leak()` — —
- `test_all_returns_deep_copy()` — —
- `test_clear_empties_registry()` — —
- `test_get_default_registry_returns_module_singleton()` — —
- `test_register_probe_decorator_uses_default_registry()` — —
- `test_decorator_does_not_pollute_user_registries()` — —
- `test_healthy_system_emits_only_all_ok()` — —
- `test_no_dsi_overlay_fires_when_overlay_missing()` — —
- `test_display_auto_detect_conflict()` — —
- `test_dsi_overlay_no_drm_connector()` — —
- `test_dsi_no_edid_panel_missing()` — —
- `test_dsi_connector_not_connected()` — —
- `test_dsi_connected_no_backlight()` — —
- `test_dsi_backlight_init_failed_extracts_error_code()` — —
- `test_no_drm_kernel_driver()` — —
- `test_dsi_driver_not_loaded()` — —
- `test_i2c_arm_not_enabled()` — —
- `test_i2c_backlight_bus_empty()` — —
- `test_compositor_not_running()` — —
- `test_wayland_socket_missing()` — —
- `test_chromium_not_running_info_only()` — —
- `test_dpms_off()` — —
- `test_no_wayland_output()` — —
- `test_all_ok_no_wayland()` — —
- `test_backlight_power_off_dynamic_rule()` — —
- `test_backlight_brightness_zero_dynamic_rule()` — —
- `test_i2c_chip_missing_dynamic_rule()` — —
- `test_rule_names_are_unique()` — —
- `test_layer_data_creation()` — —
- `test_snapshot_creation()` — —
- `test_snapshot_layer_accessor()` — —
- `test_snapshot_yaml_roundtrip()` — —
- `test_snapshot_diff_added_layer()` — —
- `test_snapshot_diff_removed_layer()` — —
- `test_snapshot_diff_modified_data()` — —


## Project Structure

📄 `CHANGELOG`
📄 `README` (1 functions)
📄 `SUMD` (150 functions)
📄 `SUMR`
📄 `docs.API` (1 functions)
📄 `docs.README` (1 functions)
📄 `examples.doql.snapshot`
📄 `examples.fraq.snapshot`
📄 `examples.redeploy.migration`
📄 `examples.redeploy.snapshot`
📄 `goal`
📄 `op3_poc`
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.duplication.toon`
📄 `project.evolution.toon`
📄 `project.integration-roadmap`
📄 `project.map.toon` (332 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `pyproject`
📦 `src.op3`
📦 `src.opstree`
📄 `src.opstree._version`
📦 `src.opstree.cli`
📦 `src.opstree.cli.commands`
📄 `src.opstree.cli.commands.convert` (1 functions)
📄 `src.opstree.cli.commands.drift` (1 functions)
📄 `src.opstree.cli.commands.scan` (1 functions)
📄 `src.opstree.cli.main` (1 functions)
📦 `src.opstree.config_apply`
📦 `src.opstree.diagnostics`
📄 `src.opstree.diagnostics.rules` (6 functions, 3 classes)
📦 `src.opstree.drift`
📄 `src.opstree.drift.detector` (2 functions, 2 classes)
📦 `src.opstree.fleet`
📄 `src.opstree.fleet.model` (1 functions, 2 classes)
📄 `src.opstree.fleet.scanner` (6 functions)
📦 `src.opstree.formats`
📄 `src.opstree.formats.less` (3 functions, 1 classes)
📄 `src.opstree.formats.migration_yaml` (2 functions, 1 classes)
📄 `src.opstree.formats.registry` (5 functions, 1 classes)
📄 `src.opstree.formats.snapshot_yaml` (2 functions, 1 classes)
📦 `src.opstree.integrations`
📄 `src.opstree.integrations.compat` (1 functions, 1 classes)
📦 `src.opstree.layers`
📄 `src.opstree.layers.builtin` (14 classes)
📄 `src.opstree.layers.tree` (6 functions, 2 classes)
📦 `src.opstree.probes`
📄 `src.opstree.probes.base` (4 functions, 3 classes)
📦 `src.opstree.probes.builtin`
📄 `src.opstree.probes.builtin.business_health` (5 functions, 1 classes)
📄 `src.opstree.probes.builtin.endpoint_http` (5 functions, 1 classes)
📄 `src.opstree.probes.builtin.os_linux` (12 functions, 2 classes)
📄 `src.opstree.probes.builtin.physical_rpi` (22 functions, 2 classes)
📄 `src.opstree.probes.builtin.rpi_diagnostics` (12 functions)
📄 `src.opstree.probes.builtin.runtime_container` (6 functions, 1 classes)
📄 `src.opstree.probes.builtin.service_containers` (5 functions, 1 classes)
📄 `src.opstree.probes.context` (4 functions, 5 classes)
📄 `src.opstree.probes.registry` (7 functions, 1 classes)
📦 `src.opstree.scanner`
📄 `src.opstree.scanner.linear` (3 functions, 1 classes)
📦 `src.opstree.snapshot`
📄 `src.opstree.snapshot.diff` (2 functions, 1 classes)
📄 `src.opstree.snapshot.model` (4 functions, 3 classes)
📄 `sumd`

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

## Automatyzacja repozytorium

- [Synchronizacja metadanych](information/org-metadata-sync.md) — koordynator, harmonogram i diagnostyka.
