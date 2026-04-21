# op3 ↔ doql ↔ redeploy — Integration Roadmap

**Status:** Draft from analysis 2026-04-21
**Current op3 version:** 0.1.14

This document records the cross-project integration plan. The analysis
originated from a review of doql v1.0.12 (which added `adopt/`, `drift/`,
`integrations/op3_bridge.py`) and the `c2004/redeploy/pi109` deployment
case study.

Only the op3-relevant parts are tracked here. Parts for doql and redeploy
are referenced but must be executed in their own repos.

---

## Audit findings (2026-04-21)

Checked against the analysis claims. Many items in the analysis are
**already done** in current op3 (v0.1.14). The analysis was written
against v0.1.4 data.

Already completed:

- **CLI split** — `cli/commands/{scan.py,drift.py,convert.py}` exists;
  `cli/main.py` is 22 lines (just the click group).
- **`__all__` exports** — defined in every package `__init__.py`
  (`opstree`, `scanner`, `probes`, `snapshot`, `drift`, `diagnostics`,
  `formats`, `layers`, `integrations`).
- **Private methods underscored** — sampled across modules; convention held.
- **Test suite** — 94 tests (analysis said 26).

Real outstanding debt:

- **Version drift across files** (5 locations):
  - `VERSION` → `0.1.14`
  - `src/opstree/__init__.py::__version__` → `0.1.14`
  - `src/opstree/_version.py::__version__` → `0.1.12` (stale)
  - `src/opstree/cli/main.py` click `version_option` → `0.1.7` (stale, hardcoded)
  - `src/opstree/cli/commands/convert.py` `scanner_version="0.1.7"` (hardcoded)
  - `src/opstree/drift/detector.py` `scanner_version="0.1.7"` (hardcoded)
  - `src/opstree/formats/snapshot_yaml.py` fallback `"0.1.7"` (stale default)
  - `src/opstree/scanner/linear.py` `scanner_version="0.1.12"` (hardcoded)
- **No dedicated `docs/API.md`** — only general `docs/README.md` (19KB).
- **No release freeze** — still 0.x, no formal API stability commitment,
  but doql v1.0.12 already depends on op3 as a production dependency.

---

## Sprint 1 — API freeze + 0.2.0 (this iteration)

Goal: make op3 a formally stable dependency for doql 1.x and upcoming
redeploy integration.

1. **Single source of version truth.**
   - `_version.py` reads `VERSION` file (or exports constant kept in sync by release tooling).
   - `opstree/__init__.py` imports `__version__` from `_version.py`.
   - `cli/main.py` uses `click.version_option(version=__version__)`.
   - Runtime code (`scanner/linear.py`, `drift/detector.py`,
     `cli/commands/convert.py`, `formats/snapshot_yaml.py`) stops
     hardcoding `scanner_version` — reads from `opstree.__version__`.
2. **Write `docs/API.md`.**
   Document the public surface committed to by 0.2.0:
   - `LayerTree`, builtin layers
   - `Snapshot`, `LayerData`, `PartialSnapshot`, `snapshot_diff`, `Change`
   - `Probe`, `ProbeContext`, `ProbeResult`, `ProbeRegistry`, `register_probe`
   - `LinearScanner`, `scan_device`, `build_layer_tree`, `build_scanner`
   - `FormatRegistry`, `register_format`
   - `DriftDetector`, `DriftReport`
   - `Diagnostic`, `Rule`, `RuleEngine`, `Severity`
   - Contract note: changes to signatures or return types of any of the
     above require a minor bump (0.2 → 0.3).
3. **Bump to 0.2.0.** Add CHANGELOG entry framing the release as "API stable".

---

## Sprint 2 — Fleet scan (DONE, shipped in [Unreleased])

Goal achieved via native implementation rather than
`fraq.adapters.HybridAdapter` wrapping. Investigation showed
`HybridAdapter` is an adapter-of-adapters for `FraqNode`, not a
snapshot merger — the original plan was based on assumed API.

Delivered:

- `opstree.fleet` subpackage: `FleetSnapshot`, `FleetVariance`,
  `scan_fleet`, `compute_variance`.
- `scan_fleet(scanner, target_execute, *, max_workers=None)` uses
  `concurrent.futures.ThreadPoolExecutor` (I/O-bound work).
- `compute_variance(snapshots)` pure function; empty/single-snapshot
  input returns `FleetVariance(fields={}, by_layer={})`.
- Per-layer count exposed via `FleetVariance.by_layer`.
- 15 new tests (`tests/unit/test_fleet.py`). Total suite 109 passed.

What this unblocks downstream:

- `doql adopt --from-fleet "tag:kiosk"` — scan cohort, derive shared
  LESS; varying fields become variants/variables.
- `redeploy drift --fleet` — verify a tag cohort in one pass.

---

## Sprint 3 — LessAdapter feature extensions (DONE, shipped in [Unreleased])

Per analysis "Option 3": doql stays the richer parser, op3 extends its
LESS adapter only with features it actually needs for round-trip.

Delivered:

- **Inline comments** — `_strip_inline_comment` strips `// ...` from any
  line before key/value extraction; backslash-aware so `\//` survives.
- **Multi-line values** — `_parse_block` continuation logic: if a line
  does not end with an unescaped `;`, subsequent lines are appended
  until the terminator appears. Leading whitespace of continuation
  lines is preserved (trailing stripped).
- **Escape sequences** — `\;` (literal semicolon), `\"` (literal quote),
  `\n` (newline), `\\` (literal backslash) in both parse and render.
- App block parsing refactored to use `_parse_block` instead of a
  hand-rolled regex, giving uniform behaviour across all blocks.
- 7 new tests; all `examples/doql/app.doql.less` and
  `examples/redeploy/app.doql.less` parse without errors (workflow
  blocks are silently skipped as out-of-scope, not hard failure).

Explicitly **out of scope for op3's LessAdapter** (stay in doql):

- `@variables`, `@import`
- Complex nested selectors beyond `app/interface/service/environment/deploy`
- `workflow` declarations

---

## Sprint 4 — AdaptiveScanner with anomaly → follow-up (DONE, shipped in [Unreleased])

Prerequisite: Sprints 1–3 complete and stable.

Delivered:

- `AdaptiveScanner` extends `LinearScanner` with `followup_registry`:
  mapping trigger layer → list of follow-up `Probe` objects. After a
  primary probe reports anomalies, every registered follow-up is asked
  `can_probe`; if eligible it is scanned and its layer added to the
  snapshot. This keeps primary probes lightweight (single pass) and
  reconciliation / deep-dive logic in follow-ups (run only when needed).
- `CompositorProbe` (`runtime.compositor`) detects Wayland compositor
  (labwc / sway / weston / wayfire) and kanshi state. Flags anomaly when
  kanshi is installed but no active profile exists.
- `KanshiReconcileProbe` (`runtime.compositor.kanshi`) follow-up probe
  registered against `physical.display`. When both DSI and HDMI
  connectors are present it suggests a dual-output kanshi profile,
  satisfying the concrete benchmark from `c2004/pi109`.
- 10 new tests covering trigger / skip / anomaly propagation.

---

## Cross-project items (not op3, but op3 participates)

Tracked here for context; execute in the owning repo.

- **doql** — `PARSER_AUDIT.md` comparing doql LESS parser vs op3
  `LessAdapter`. Precondition for Sprint 3 decisions on both sides.
- **doql** — parity test `adopt --from-device → build` using op3
  as the device scanner.
- **redeploy** — `redeploy drift` command built on `op3.DriftDetector`
  (new capability, strangler-fig style).
- **c2004/redeploy/pi109** — `manifest.yaml` orchestrator draft, links
  `migration.md`, `resume.md`, `waveshare-8-inch.md`, and invokes
  `op3 drift` as verification phase.

---

## Open questions

- Should `_version.py` be auto-generated by release tooling or hand-edited?
  Current preference: single literal in `_version.py`, `VERSION` file
  is a build artifact (or vice versa — pick one).
- After Sprint 1, does doql pin `op3 >= 0.2, < 0.3` or `>= 0.2`?
  Recommend pinning minor during the 0.x phase even after "API stable".
