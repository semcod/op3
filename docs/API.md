# op3 — Public API Reference

**Version:** 0.2.0 (API stable)

This document is the authoritative contract for the public surface of
the `opstree` package. Downstream projects (`doql`, `redeploy`, `fraq`)
depend on these symbols; breaking changes require a minor version bump
while op3 remains on the 0.x line, and a major bump once op3 reaches
1.0.

Anything **not** listed here is implementation detail and may change
without notice, even in patch releases. In particular: modules under
`opstree.probes.builtin.*`, `opstree.layers.builtin.*` constants, and
any symbol whose name starts with an underscore.

All imports below are rooted at the `opstree` package.

---

## Version

```python
from opstree import __version__
```

`__version__` is the single source of truth. It is re-exported from
`opstree._version` and kept in sync with the `VERSION` file and the
`pyproject.toml` `[project].version` field by the release process.

Runtime code that needs to stamp a snapshot (`scanner_version`) or
render a tool banner MUST read `__version__` rather than hardcoding a
literal.

---

## Layers

```python
from opstree import LayerTree, PhysicalLayer, OsLayer, RuntimeLayer, ServiceLayer, EndpointLayer, BusinessLayer
```

### `LayerTree`

Topologically-ordered registry of layer definitions.

```python
tree = LayerTree()
tree.register(PhysicalLayer.display)   # LayerDefinition
tree.get("physical.display")           # -> LayerDefinition | None
tree.topological_order()               # -> list[str]
tree.to_fraq_node()                    # -> fraq.FraqNode
```

Registering the same layer id twice raises `ValueError`. Cycles in
`depends_on` raise `ValueError("Cycle detected in layer dependencies")`
from `topological_order`.

### Builtin layer bundles

`PhysicalLayer`, `OsLayer`, `RuntimeLayer`, `ServiceLayer`,
`EndpointLayer`, `BusinessLayer` are namespaces whose attributes are
`LayerDefinition` instances. The layer ids exposed today:

- `physical.display`, `physical.network`, `physical.compute`
- `os.kernel`, `os.config`
- `runtime.container`, `runtime.compositor`
- `service.containers`, `service.systemd`
- `endpoint.http`, `endpoint.tcp`
- `business.health`

New layer ids may be added in minor releases; **removal or rename of an
existing id is a breaking change**.

---

## Snapshot

```python
from opstree import Snapshot, LayerData, PartialSnapshot, snapshot_diff, Change
```

### `Snapshot` (frozen pydantic model)

Fields:

- `target: str`
- `scanned_at: datetime`
- `scanner_version: str`
- `layers: dict[str, LayerData]`
- `anomalies: list`

Methods:

- `.layer(layer_id: str) -> LayerData | None`
- `.query(jmespath_expr: str) -> Any`
- `.to_yaml() -> str`
- `Snapshot.load(path) -> Snapshot` (classmethod; YAML on disk)

### `LayerData` (frozen pydantic model)

Fields: `layer_id`, `probed_at`, `probed_by`, `data: dict`,
`raw_evidence: dict`.

### `PartialSnapshot` (frozen pydantic model)

Fields: `layers: dict[str, LayerData]`, `source_format: str`,
`source_path: str | None`. Produced by format adapters when reading
config files that don't cover every layer.

### `snapshot_diff(a: Snapshot, b: Snapshot) -> list[Change]`

Returns a list of `Change` records describing the transition
`a -> b`.

### `Change` (frozen dataclass)

Fields: `layer_id`, `path`, `type` (`"added" | "removed" | "modified"`),
`old_value`, `new_value`.

---

## Probes

```python
from opstree import Probe, ProbeContext, ProbeResult, ProbeRegistry, register_probe
```

### `Probe` (protocol)

Required attributes: `layer_id: str`, `probe_name: str`.

Required methods:

- `can_probe(ctx: ProbeContext) -> bool`
- `scan(ctx: ProbeContext) -> ProbeResult`
- `anomalies(data: LayerData) -> list`

### `ProbeContext` (dataclass)

Fields: `target: str`, `execute: callable`, `metadata: dict`.

The `execute` callable is domain-specific (local shell, SSH,
ansible-over-ssh, …). Probes MUST NOT import transport libraries
directly — they only call `ctx.execute(cmd: str)` and interpret the
return value.

### `ProbeResult` (dataclass)

Fields: `layer_data: LayerData`, `success: bool`,
`error: str | None`.

### `ProbeRegistry`

Instance methods: `register(probe)`, `get(layer_id) -> list[Probe]`,
`all() -> dict[str, list[Probe]]`, `clear()`.

Each instance owns its own probe dict — create a fresh registry per
scanner for isolation.

### `register_probe` (decorator)

Instantiates the decorated class and registers it on the module-global
default registry. Application code should usually create its own
`ProbeRegistry` instead.

---

## Scanner

```python
from opstree import LinearScanner, AdaptiveScanner, scan_device, build_layer_tree, build_scanner
```

### `LinearScanner`

Sequential scanner driven by a `LayerTree` + `ProbeRegistry`.

```python
scanner = LinearScanner(layer_tree)
scanner.probe_registry = my_registry   # default is an empty ProbeRegistry()
snapshot = scanner.scan(target="pi@host", execute=ssh_exec_fn)
```

`scanner.scan` stamps the returned `Snapshot.scanner_version` with
`opstree.__version__`.

### `AdaptiveScanner`

Extends `LinearScanner` with follow-up probe capability. When a primary
probe reports anomalies, registered follow-up probes for that layer are
executed conditionally.

```python
scanner = AdaptiveScanner(layer_tree)
scanner.probe_registry = my_registry
scanner.register_followup("physical.display", kanshi_reconcile_probe)
snapshot = scanner.scan(target="pi@host", execute=ssh_exec_fn)
```

Methods:
- `register_followup(trigger_layer: str, probe: Probe) -> None` — register
  a follow-up probe to run when `trigger_layer` reports anomalies

Follow-up probes are only invoked when:
1. The trigger layer reports at least one anomaly
2. The follow-up probe's `can_probe(ctx)` returns `True`

This pattern keeps lightweight anomaly detection in the primary probe (same
pass) and heavy reconciliation logic in follow-ups (run only when needed).

### `scan_device(target, execute, layer_tree) -> Snapshot`

Convenience one-liner equivalent to
`LinearScanner(layer_tree).scan(target, execute)`.

Note: `scan_device` uses an **empty** default probe registry. For a
fully-wired scanner, prefer `build_scanner(...)`.

### `build_layer_tree(layer_ids: Sequence[str]) -> LayerTree`

Builds a `LayerTree` from the given layer ids plus their transitive
`depends_on`. Raises `ValueError` on unknown ids.

### `build_scanner(layer_ids, *, extra_probes=None, include_default_probes=True) -> LinearScanner`

Returns a fully-wired `LinearScanner` with builtin probes registered for
each layer in `layer_ids` (and their deps). Pass `extra_probes` to add
custom probes; pass `include_default_probes=False` to skip builtins.

---

## Fleet

```python
from opstree import FleetSnapshot, FleetVariance, compute_variance, scan_fleet, render_common_as_snapshot, render_variant_matrix
```

Added in 0.2.0. Groups N :class:`Snapshot` results together with a
summary of fields that differ across them.

### `FleetVariance` (frozen pydantic model)

Fields:

- `fields: dict[str, dict[str, Any]]` — path → {target: value} for
  every path where values diverge across the fleet.
- `by_layer: dict[str, int]` — count of diverging paths per layer id.

Properties:

- `.is_uniform` — `True` iff no fields diverge.
- `.diverging_paths` — sorted list of divergent paths.

Paths look like `"<layer_id>.data.<field>[.<subfield>…]"`. When a layer
is absent on some hosts, every path under that layer is still flagged,
with the absent side recorded as `None`.

### `FleetSnapshot` (frozen pydantic model)

Fields:

- `targets: list[str]` — preserved in caller iteration order.
- `snapshots: dict[str, Snapshot]` — keyed by target.
- `variance: FleetVariance`.

Properties / methods:

- `.size -> int`
- `.for_target(target: str) -> Snapshot | None`

### `compute_variance(snapshots: Mapping[str, Snapshot]) -> FleetVariance`

Pure, deterministic. Fewer than two snapshots yields an empty
(`is_uniform`) variance. Only the `data` dict of each `LayerData` is
compared — `probed_at`, `probed_by`, and `raw_evidence` are excluded so
per-host timing jitter doesn't register as drift.

### `scan_fleet(scanner, target_execute, *, max_workers=None) -> FleetSnapshot`

Runs ``scanner.scan(target, execute_fn)`` concurrently for every
``(target, execute_fn)`` pair in ``target_execute``. The scanner's
layer tree and probe registry are read-only during a scan, so one
wired scanner (typically from :func:`build_scanner`) is safe to reuse
across threads.

`max_workers` defaults to `min(32, len(target_execute))`. Per-target
exceptions propagate — there is no silent partial-success mode yet.

Recipe — scan a fleet over SSH:

```python
from opstree import build_scanner, scan_fleet
from opstree.probes.context import SSHContext

scanner = build_scanner(["os.kernel", "runtime.container"])
target_execute = {
    f"pi@{host}": SSHContext(f"pi@{host}").execute
    for host in ("10.0.0.10", "10.0.0.11", "10.0.0.12")
}
fleet = scan_fleet(scanner, target_execute)
for path in fleet.variance.diverging_paths:
    print(path, fleet.variance.fields[path])
```

---

## Drift

```python
from opstree import DriftDetector, DriftReport
```

### `DriftDetector`

```python
detector = DriftDetector()
report = detector.detect(intended: PartialSnapshot, actual: Snapshot)
```

`intended` typically comes from a format adapter (`LessAdapter.parse(...)`,
`MigrationYamlAdapter.parse(...)`); `actual` from a fresh scan.

### `DriftReport` (dataclass)

Fields: `intended_source`, `actual_target`, `has_drift`,
`changes: list[Change]`, `summary: dict`.

`summary` contains `{"total_changes": int, "by_type": {...},
"by_layer": {...}}`.

---

## Formats

```python
from opstree import FormatRegistry, register_format
```

### `FormatRegistry`

Classmethods (wraps `fraq.formats.FormatRegistry`):
`register(name, adapter=None)`, `get(name)`, `available() -> list[str]`,
`serialize(name, data, **kwargs)`.

### `register_format(name, adapter=None)` (decorator)

Format adapters currently shipped: `less`, `migration_yaml`,
`snapshot_yaml`. They are intentionally **not** re-exported from the
top-level package — import them from
`opstree.formats.less`, `opstree.formats.migration_yaml`,
`opstree.formats.snapshot_yaml` if you need the adapter classes
directly. This keeps the top-level API surface small and lets us
reshape the adapter internals without breaking downstream imports.

### `LessAdapter` (stable since 0.2.0)

The LESS adapter is the bridge between ``.doql.less`` configuration
files and op3's :class:`Snapshot` / :class:`PartialSnapshot` models.
It intentionally covers **only** the subset of LESS syntax needed for
round-tripping the layers op3 understands (``app``, ``interface``,
``service``, ``environment``, ``deploy``). Advanced constructs such as
``@variables``, ``@import``, nested selectors beyond those five blocks,
and ``workflow`` declarations are out of scope — they live in the richer
doql parser.

Supported in ``parse`` and ``render``:

- **Inline comments** — ``// comment`` suffixes on any line are
  stripped before key/value extraction.
- **Multi-line values** — a value whose first line does not end with
  an unescaped ``;`` continues onto subsequent lines until the
  terminator appears. Leading whitespace of continuation lines is
  preserved (trailing only is stripped) so indented heredocs survive.
- **Escape sequences** — ``\;`` (literal semicolon), ``\"`` (literal
  quote), ``\n`` (newline), and ``\\`` (literal backslash). On render,
  ``;``, ``"``, and ``\`` are automatically escaped so the output is
  safe to re-parse.

---

## Diagnostics

```python
from opstree import Diagnostic, Rule, RuleEngine, Severity
```

Generic rule engine used by the builtin RPi diagnostics and by
downstream projects (`redeploy`, `doql`) for their own rule sets.

### `Severity`

Literal type: `"info" | "warning" | "error" | "critical"`.

### `Diagnostic` (frozen dataclass)

Fields: `component: str`, `severity: Severity`, `message: str`,
`fix: str | None`, `rule_name: str | None`, `evidence: dict`.

Method: `.to_dict() -> dict`.

### `Rule[T]` (dataclass, generic over subject type `T`)

Fields:

- `name: str`
- `component: str`
- `severity: Severity = "warning"`
- `predicate: Callable[[T], bool] | None`
- `message: Callable[[T], str] | str | None`
- `fix: Callable[[T], str] | str | None`
- `evidence: Callable[[T], dict] | None`
- `dynamic: Callable[[T], Iterable[Diagnostic]] | None`

Exactly one of `predicate` or `dynamic` must be provided (enforced in
`__post_init__`, raises `ValueError` otherwise).

Method: `.evaluate(subject: T) -> list[Diagnostic]`.

### `RuleEngine[T]`

- Constructor: `RuleEngine(rules: Iterable[Rule[T]])`
- `.rules -> list[Rule[T]]`
- `.evaluate(subject: T) -> list[Diagnostic]`
- `.any_error(subject, *, exclude: Iterable[str] = ()) -> bool`

---

## CLI (stable invocations)

Entry point: `op3` (defined in `[project.scripts]`).

Subcommands:

- `op3 scan [TARGET] [--ssh] [--layers ...] [--output PATH] [--format yaml|json]`
- `op3 drift INTENDED_FILE [TARGET] ...`
- `op3 convert INPUT_FILE OUTPUT_FILE --format less|migration_yaml|snapshot_yaml`
- `op3 --version`

Subcommand option names are part of the stable CLI contract. Additional
options may be added in minor releases; removal or rename is breaking.

---

## What is explicitly NOT part of the public API

These exist and may be imported, but no stability is promised:

- Everything under `opstree.probes.builtin.*` — internal probes
- Everything under `opstree.layers.builtin.*` constants (except the
  `*Layer` namespaces listed above)
- `opstree.scanner.build._resolve_dependencies`,
  `_default_probe_factory`, `_BUILTIN_LAYERS`
- `opstree.probes.registry._default_registry`,
  `get_default_registry` (escape hatch for migration, may go away)
- The `opstree.integrations.compat` module (compatibility shims)
- The top-level `op3` package (`src/op3/__init__.py`) — it only
  re-exports `__version__` today; treat `opstree` as the real package

---

## Versioning policy (0.x → 1.0)

While op3 is on 0.x:

- **Patch** (`0.2.0 -> 0.2.1`): bugfixes, new probes / layers /
  format adapters that don't touch public signatures.
- **Minor** (`0.2.x -> 0.3.0`): any change to a signature, return
  type, or removal listed in this document.
- Downstream projects SHOULD pin as `op3 >= 0.2, < 0.3`.

1.0 will be cut once the API has survived one full release cycle of
`doql` and `redeploy` depending on it without churn.
