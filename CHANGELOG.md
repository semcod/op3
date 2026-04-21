# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — Sprint 3: LessAdapter feature extensions
- `LessAdapter` now supports **inline comments** (`// ...` stripped
  from any line before key/value extraction), **multi-line values**
  (continuation until an unescaped `;`), and **escape sequences**
  (`\;`, `\"`, `\n`, `\\`).
- `render` automatically escapes `;`, `"`, and `\` so re-parsing is
  safe.
- App block parsing (`app { ... }`) refactored to use `_parse_block`
  instead of a hand-rolled regex, ensuring comments / escapes / multi-line
  are handled uniformly with every other block.
- 7 new tests covering inline comments, multi-line values,
  escaped-semicolon continuation, `\n` and `\\` unescape,
  render escape, and round-trip preservation.

### Added — Sprint 2: fleet scanning
- `opstree.fleet` subpackage — `FleetSnapshot`, `FleetVariance`,
  `scan_fleet`, `compute_variance`.
- `scan_fleet(scanner, target_execute, *, max_workers=None)` runs one
  wired `LinearScanner` against N targets concurrently via a thread
  pool (I/O-bound work — SSH / subprocess round trips).
- `compute_variance` is a pure function that flattens each snapshot's
  layer data and records every path whose value disagrees across the
  fleet; intended for `doql adopt --from-fleet` and
  `redeploy drift --fleet`.
- 15 new tests in `tests/unit/test_fleet.py` covering empty / single /
  uniform / divergent / partial-layer / ordering-independence /
  nested-equality variance cases and end-to-end `scan_fleet` via
  `MockContext`.
- `docs/API.md` gains a "Fleet" section documenting the new surface.

Rationale: the original roadmap suggested wrapping
`fraq.adapters.HybridAdapter`, but that class is an
adapter-of-adapters for `FraqNode` — it does not provide snapshot
merging semantics. A native implementation based on
`opstree.snapshot` primitives is simpler, transport-agnostic, and keeps
`fraq` as a dependency for what it actually does well.

## [0.2.3] - 2026-04-21

### Docs
- Update README.md

## [0.2.2] - 2026-04-21

### Docs
- Update CHANGELOG.md
- Update README.md
- Update docs/API.md
- Update project/integration-roadmap.md

### Test
- Update tests/unit/test_formats/test_less_adapter.py

## [0.2.1] - 2026-04-21

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/API.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md
- Update project/integration-roadmap.md

### Test
- Update tests/unit/test_fleet.py

### Other
- Update VERSION
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- ... and 9 more files

## [0.2.0] - 2026-04-21

API stability declaration. This release does not change any public
signature; it formalises the contract so downstream projects
(`doql` 1.x, upcoming `redeploy` integration) can pin against a stable
minor line.

### Added
- `docs/API.md` — authoritative public API reference. Anything not
  listed there is implementation detail.
- `project/integration-roadmap.md` — cross-project plan for
  `op3 ↔ doql ↔ redeploy` integration (Sprint 1–4 for op3).
- `opstree.__version__` is now re-exported from `opstree._version` and
  is the single source of truth for all runtime version stamping.

### Changed
- **Version drift eliminated.** Five locations previously hardcoded
  stale literals (`"0.1.7"`, `"0.1.12"`): `cli/main.py`
  `version_option`, `scanner/linear.py`, `drift/detector.py`,
  `cli/commands/convert.py`, `formats/snapshot_yaml.py`. All now read
  `__version__` from `opstree._version`.
- `src/op3/__init__.py` re-exports `__version__` from `opstree._version`
  instead of carrying its own literal.

### Docs
- Update VERSION to 0.2.0
- Update pyproject.toml version to 0.2.0

## [0.1.14] - 2026-04-21

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 8 more files

## [0.1.13] - 2026-04-21

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/unit/test_integrations_compat.py

### Other
- Update VERSION
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 9 more files

## [0.1.11] - 2026-04-21

### Docs
- Update README.md

### Test
- Update tests/integration/test_rpi_hardware_pipeline.py
- Update tests/unit/test_diagnostics.py
- Update tests/unit/test_rpi_diagnostics.py

### Other
- Update VERSION

## [0.1.9] - 2026-04-21

### Docs
- Update README.md

### Test
- Update tests/unit/test_build_scanner.py
- Update tests/unit/test_probe_registry.py

## [0.1.8] - 2026-04-21

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md

### Test
- Update tests/unit/test_formats/test_less_adapter.py
- Update tests/unit/test_snapshot.py

### Other
- Update project/duplication.toon.yaml
- Update project/map.toon.yaml
- Update sumd.json

## [0.1.7] - 2026-04-21

### Docs
- Update README.md

## [0.1.6] - 2026-04-21

### Docs
- Update README.md

### Test
- Update tests/unit/test_formats/test_less_adapter.py
- Update tests/unit/test_snapshot.py

## [0.1.5] - 2026-04-21

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/unit/test_formats/test_less_adapter.py
- Update tests/unit/test_snapshot.py

### Other
- Update app.doql.less
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/duplication.toon.yaml
- Update project/evolution.toon.yaml
- ... and 8 more files

## [0.1.4] - 2026-04-21

### Docs
- Update README.md

### Other
- Update .env.example

## [0.1.3] - 2026-04-21

### Docs
- Update README.md
- Update op3_poc.md

### Test
- Update tests/conftest.py
- Update tests/fixtures/sample.doql.less
- Update tests/fixtures/sample.migration.yaml
- Update tests/fixtures/sample.snapshot.yaml
- Update tests/integration/test_cli.py
- Update tests/integration/test_full_scan.py
- Update tests/unit/test_formats/test_less_adapter.py
- Update tests/unit/test_layers.py
- Update tests/unit/test_snapshot.py

### Other
- Update .env.example
- Update .gitignore
- Update VERSION
- Update examples/doql/app.doql.less
- Update examples/doql/snapshot.yaml
- Update examples/fraq/app.doql.less
- Update examples/fraq/snapshot.yaml
- Update examples/redeploy/app.doql.less
- Update examples/redeploy/migration.yaml
- Update examples/redeploy/snapshot.yaml

## [0.1.1] - 2026-04-21

### Docs
- Update README.md

### Test
- Update tests/test_op3.py

### Other
- Update .env
- Update .env.example
- Update VERSION

## [0.0.1] - 2026-04-21

### Other
- Update .gitignore
- Update project.sh

