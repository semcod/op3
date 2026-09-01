"""Compositor & kanshi follow-up probes for the ``runtime.compositor`` layer.

Primary probe: :class:`CompositorProbe` (``runtime.compositor``).
Follow-up probe: :class:`KanshiReconcileProbe` (``runtime.compositor.kanshi``)
run by :class:`AdaptiveScanner` when the physical display layer reports
both DSI and HDMI connected simultaneously.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from opstree.probes.base import ProbeContext, ProbeResult
from opstree.probes.builtin.exec_adapter import ProbeExec
from opstree.snapshot.model import LayerData

_Exec = ProbeExec  # backward-compatible alias for tests and internal callers


class CompositorProbe:
    """Detect Wayland compositor and kanshi availability."""

    layer_id = "runtime.compositor"
    probe_name = "compositor"

    # ── lifecycle ─────────────────────────────────────────────────────

    def can_probe(self, ctx: ProbeContext) -> bool:
        # Needs a Wayland socket or kanshi binary to be present.
        return (
            _Exec.run(ctx, "ls /run/user/$(id -u)/ 2>/dev/null | grep '^wayland-'").ok
            or _Exec.run(ctx, "which kanshi 2>/dev/null").ok
        )

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        compositor = self._detect_compositor(ctx)
        kanshi = _Exec.run(ctx, "which kanshi 2>/dev/null")
        profiles: list[dict[str, Any]] = []
        active_profile: str | None = None

        if kanshi.ok:
            profiles = self._list_kanshi_profiles(ctx)
            active_profile = self._detect_active_profile(ctx)

        data: dict[str, Any] = {
            "compositor": compositor,
            "version": self._compositor_version(ctx, compositor),
            "kanshi_enabled": kanshi.ok,
            "kanshi_profiles": profiles,
            "active_profile": active_profile,
        }
        return ProbeResult(
            layer_data=LayerData(
                layer_id=self.layer_id,
                probed_at=datetime.now(timezone.utc),
                probed_by=self.probe_name,
                data=data,
                raw_evidence={},
            ),
            success=True,
        )

    def anomalies(self, data: LayerData) -> list:
        """Flag when kanshi is available but no active profile."""
        anomalies: list = []
        d = data.data
        if d.get("kanshi_enabled") and not d.get("active_profile"):
            anomalies.append(
                {
                    "severity": "warning",
                    "layer": self.layer_id,
                    "message": "kanshi installed but no active profile — output routing may drift",
                    "evidence": {"profiles": d.get("kanshi_profiles", [])},
                }
            )
        return anomalies

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _detect_compositor(ctx: ProbeContext) -> str:
        for name in ("labwc", "sway", "weston", "wayfire"):
            if _Exec.run(ctx, f"pgrep -x '{name}' 2>/dev/null").ok:
                return name
        return "unknown"

    @staticmethod
    def _compositor_version(ctx: ProbeContext, name: str) -> str:
        if name == "labwc":
            r = _Exec.run(ctx, "labwc --version 2>/dev/null")
            return r.text("").split()[-1] if r.ok else ""
        if name == "sway":
            r = _Exec.run(ctx, "sway --version 2>/dev/null | head -1")
            return r.text("").split()[-1] if r.ok else ""
        return ""

    @staticmethod
    def _list_kanshi_profiles(ctx: ProbeContext) -> list[dict[str, Any]]:
        """Parse ``~/.config/kanshi/config`` into profile dicts."""
        r = _Exec.run(ctx, "cat ~/.config/kanshi/config 2>/dev/null")
        if not r.ok:
            return []
        profiles: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for line in r.stdout.splitlines():
            line = line.strip()
            if "{" in line:
                current = {"outputs": [], "exec": []}
                # Check if profile name is on same line before the brace
                name_part = line.split("{")[0].strip()
                if name_part:
                    current["name"] = name_part
                continue
            if line.startswith("}") and current is not None:
                profiles.append(current)
                current = None
                continue
            if current is None:
                continue
            if line.startswith("output"):
                current["outputs"].append(line)
            elif line.startswith("exec"):
                current["exec"].append(line)
            elif line:
                # profile name or other directive
                current.setdefault("name", line)
        return profiles

    @staticmethod
    def _detect_active_profile(ctx: ProbeContext) -> str | None:
        # Best-effort: look at kanshi process args or swaymsg.
        r = _Exec.run(ctx, "ps -o args= -p $(pgrep -x kanshi) 2>/dev/null")
        if r.ok and r.stdout.strip():
            # kanshi started with a config file?
            for part in r.stdout.strip().split():
                if "config" in part:
                    return part
        return None


class KanshiReconcileProbe:
    """Follow-up probe: suggest a kanshi profile when DSI+HDMI are both connected.

    Registered against ``physical.display`` in :class:`AdaptiveScanner`.
    Scans kanshi state and proposes a dual-output profile based on current
    DRM connector names.
    """

    layer_id = "runtime.compositor.kanshi"
    probe_name = "kanshi_reconcile"

    # ── lifecycle ─────────────────────────────────────────────────────

    def can_probe(self, ctx: ProbeContext) -> bool:
        return _Exec.run(ctx, "which kanshi 2>/dev/null").ok

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        # Collect enough to suggest a profile.
        profiles = CompositorProbe._list_kanshi_profiles(ctx)
        # Best-effort DRM connector names from sysfs.
        drm = _Exec.run(ctx, "ls /sys/class/drm/ 2>/dev/null | grep '^card[0-9]-'")
        connectors: list[str] = drm.lines() if drm.ok else []

        suggested = self._suggest_profile(connectors)

        data: dict[str, Any] = {
            "existing_profiles": len(profiles),
            "drm_connectors": connectors,
            "suggested_profile": suggested,
            "reconcile_needed": bool(suggested),
        }
        return ProbeResult(
            layer_data=LayerData(
                layer_id=self.layer_id,
                probed_at=datetime.now(timezone.utc),
                probed_by=self.probe_name,
                data=data,
                raw_evidence={},
            ),
            success=True,
        )

    def anomalies(self, data: LayerData) -> list:
        """Report when a new profile is suggested."""
        d = data.data
        if d.get("reconcile_needed"):
            return [
                {
                    "severity": "info",
                    "layer": self.layer_id,
                    "message": "Suggested kanshi profile for dual-output configuration",
                    "evidence": {
                        "connectors": d.get("drm_connectors", []),
                        "profile": d.get("suggested_profile"),
                    },
                }
            ]
        return []

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _suggest_profile(connectors: list[str]) -> dict[str, Any] | None:
        dsi = [c for c in connectors if "DSI" in c]
        hdmi = [c for c in connectors if "HDMI" in c]
        if not (dsi and hdmi):
            return None
        return {
            "name": "dual-display",
            "outputs": [
                f"output {dsi[0]} enable",
                f"output {hdmi[0]} enable position 0,0",
            ],
            "exec": [],
        }
