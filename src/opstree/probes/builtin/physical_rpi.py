"""Physical RPi hardware probe — DSI, DRM, backlight, I2C, dmesg, kernel modules, Wayland.

Extended in op3 0.1.10 to cover the same surface previously owned by
``redeploy/detect/hardware.py`` so that:

* the rich diagnostic rule set in :mod:`opstree.probes.builtin.rpi_diagnostics`
  has everything it needs from a single layer snapshot, and
* ``redeploy`` can collapse to a thin adapter around this probe.

Layer: ``physical.display``.

Output ``LayerData.data`` keys (all stable; rules rely on them):

    board_model              str
    kernel                   str
    config_txt               str
    config_txt_path          str
    dsi_overlays             list[str]
    drm_outputs              list[dict]
    wlr_outputs              list[dict]
    backlights               list[dict]
    framebuffers             list[str]
    i2c_buses                list[dict]
    dsi_dmesg                list[str]
    dsi_dmesg_errors         list[str]
    kernel_modules           list[str]
    wayland_sockets          list[str]
    compositor_processes     dict[str, list[int]]
    kms_enabled              bool
    kms_driver               str
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from opstree.probes.base import ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


_DMESG_ERR_RE = re.compile(
    r"fail|error|unable|timeout|ERORR|cannot|denied|-\d+\]", re.IGNORECASE
)


@dataclass(frozen=True)
class _Exec:
    """Uniform adapter over the two shapes ``ProbeContext.execute`` returns.

    Historically some probes returned an ``ExecuteResult`` object (with
    ``.ok`` / ``.stdout``) while others returned a plain 3-tuple.  This
    adapter hides that so helpers can stay tidy.
    """

    ok: bool
    stdout: str

    @classmethod
    def run(cls, ctx: ProbeContext, cmd: str) -> "_Exec":
        r = ctx.execute(cmd)
        if hasattr(r, "ok"):
            return cls(ok=bool(r.ok), stdout=getattr(r, "stdout", "") or "")
        # tuple: (stdout, stderr, rc)
        try:
            stdout, _stderr, rc = r
        except Exception:
            return cls(ok=False, stdout="")
        return cls(ok=(rc == 0), stdout=stdout or "")

    def lines(self) -> list[str]:
        return [l for l in self.stdout.splitlines() if l.strip()]

    def text(self, default: str = "") -> str:
        return self.stdout.strip() if self.ok else default

    def int_(self, default: int = 0) -> int:
        if not self.ok:
            return default
        try:
            return int(self.stdout.strip())
        except (TypeError, ValueError):
            return default


class RpiPhysicalDisplayProbe:
    """Full hardware probe for a Raspberry Pi-class board."""

    layer_id = "physical.display"
    probe_name = "rpi_physical_display"

    # ── lifecycle ─────────────────────────────────────────────────────

    def can_probe(self, ctx: ProbeContext) -> bool:
        r = _Exec.run(
            ctx,
            "test -f /sys/firmware/devicetree/base/model && "
            "cat /sys/firmware/devicetree/base/model",
        )
        return r.ok and "Raspberry Pi" in r.stdout

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        config_txt, config_txt_path = self._probe_config_txt(ctx)
        dsi_overlays = self._extract_dsi_overlays(config_txt)

        drm_outputs = self._scan_drm(ctx)
        wlr_outputs = self._probe_wlr_randr(ctx)
        self._merge_wlr_into_drm(drm_outputs, wlr_outputs)

        dmesg = self._probe_dsi_dmesg(ctx)
        data: dict[str, Any] = {
            "board_model": self._probe_board_model(ctx),
            "kernel": _Exec.run(ctx, "uname -r").text(""),
            "config_txt": config_txt,
            "config_txt_path": config_txt_path,
            "dsi_overlays": dsi_overlays,
            "drm_outputs": drm_outputs,
            "wlr_outputs": wlr_outputs,
            "backlights": self._scan_backlights(ctx),
            "framebuffers": self._probe_framebuffers(ctx),
            "i2c_buses": self._probe_i2c_buses(ctx),
            "dsi_dmesg": dmesg,
            "dsi_dmesg_errors": [l for l in dmesg if _DMESG_ERR_RE.search(l)],
            "kernel_modules": self._probe_kernel_modules(ctx),
            "wayland_sockets": self._probe_wayland_sockets(ctx),
            "compositor_processes": self._probe_compositor_processes(ctx),
            "kms_enabled": self._check_kms(ctx),
            "kms_driver": self._get_kms_driver(ctx),
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

    # ── anomalies (lightweight; the rich rule set lives in diagnostics) ─

    def anomalies(self, data: LayerData) -> list:
        anomalies: list = []
        outputs = data.data.get("drm_outputs", [])
        connected = [o for o in outputs if o.get("status") == "connected"]

        if len(connected) > 1:
            dsi = [o for o in connected if "DSI" in o.get("name", "")]
            hdmi = [o for o in connected if "HDMI" in o.get("name", "")]
            if dsi and hdmi:
                anomalies.append({
                    "severity": "warning",
                    "layer": self.layer_id,
                    "message": "Both DSI and HDMI displays connected — output routing ambiguous",
                    "evidence": {"connected_outputs": [o["name"] for o in connected]},
                })
        return anomalies

    # ── individual probes ─────────────────────────────────────────────

    def _probe_board_model(self, ctx: ProbeContext) -> str:
        return _Exec.run(
            ctx,
            "cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\\0'",
        ).text("unknown")

    def _probe_config_txt(self, ctx: ProbeContext) -> tuple[str, str]:
        for path in ("/boot/firmware/config.txt", "/boot/config.txt"):
            r = _Exec.run(ctx, f"cat {path} 2>/dev/null")
            if r.ok and r.stdout.strip():
                return r.stdout, path
        return "", "/boot/firmware/config.txt"

    @staticmethod
    def _extract_dsi_overlays(config_txt: str) -> list[str]:
        return [
            line.strip()
            for line in config_txt.splitlines()
            if re.match(r"\s*dtoverlay=.*dsi", line, re.IGNORECASE)
            and not line.strip().startswith("#")
        ]

    def _scan_drm(self, ctx: ProbeContext) -> list[dict]:
        outputs: list[dict] = []
        listing = _Exec.run(ctx, "ls /sys/class/drm/ 2>/dev/null")
        if not listing.ok:
            return outputs

        for entry in listing.lines():
            if not re.match(r"^card\d+-.+", entry):
                continue
            m = re.match(r"^(card\d+)-(.*)", entry)
            if not m:
                continue
            connector = m.group(2)

            status = _Exec.run(ctx, f"cat /sys/class/drm/{entry}/status 2>/dev/null")
            enabled = _Exec.run(ctx, f"cat /sys/class/drm/{entry}/enabled 2>/dev/null")
            edid = _Exec.run(ctx, f"wc -c < /sys/class/drm/{entry}/edid 2>/dev/null")
            dpms = _Exec.run(ctx, f"cat /sys/class/drm/{entry}/dpms 2>/dev/null")

            dpms_text = dpms.text("")
            outputs.append({
                "name": entry,
                "connector": connector,
                "status": status.text("unknown"),
                "enabled": enabled.text("unknown"),
                "edid_bytes": edid.int_(0),
                # keep historic field and new, redeploy-compatible field
                "dpms": dpms_text or "unknown",
                "power_state": dpms_text or None,
                "sysfs_path": f"/sys/class/drm/{entry}",
                "modes": [],
                "transform": "normal",
                "scale": "1.0",
                "position": "0,0",
            })
        return outputs

    def _probe_wlr_randr(self, ctx: ProbeContext) -> list[dict]:
        results: list[dict] = []
        for sock in ("wayland-0", "wayland-1"):
            r = _Exec.run(
                ctx,
                f"WAYLAND_DISPLAY={sock} XDG_RUNTIME_DIR=/run/user/$(id -u) "
                "wlr-randr 2>/dev/null",
            )
            if not (r.ok and r.stdout.strip()):
                continue

            current: dict = {}
            for line in r.stdout.splitlines():
                if re.match(r"^[A-Z]", line) and '"' in line:
                    if current:
                        results.append(current)
                    name_m = re.match(r'^(\S+)\s+"([^"]*)"', line)
                    current = {
                        "output": name_m.group(1) if name_m else line.split()[0],
                        "enabled": None,
                        "mode": None,
                        "transform": None,
                        "scale": None,
                    }
                elif "Enabled:" in line:
                    current["enabled"] = "yes" in line
                elif "px," in line and ("preferred" in line or "current" in line):
                    m = re.search(r"(\d+x\d+)\s+px,\s+([\d.]+)\s+Hz", line)
                    if m:
                        current["mode"] = f"{m.group(1)}@{float(m.group(2)):.0f}"
                elif "Transform:" in line:
                    current["transform"] = line.split(":", 1)[1].strip()
                elif "Scale:" in line:
                    current["scale"] = line.split(":", 1)[1].strip()
            if current:
                results.append(current)
            break
        return results

    @staticmethod
    def _merge_wlr_into_drm(drm_outputs: list[dict], wlr_outputs: list[dict]) -> None:
        for wo in wlr_outputs:
            name = wo.get("output", "")
            for drm in drm_outputs:
                if drm.get("connector") != name:
                    continue
                if wo.get("mode"):
                    drm["modes"] = [wo["mode"]]
                if wo.get("transform"):
                    drm["transform"] = wo["transform"]
                if wo.get("scale"):
                    drm["scale"] = wo["scale"]
                if wo.get("enabled") is not None:
                    drm["enabled"] = "enabled" if wo["enabled"] else "disabled"

    def _scan_backlights(self, ctx: ProbeContext) -> list[dict]:
        out: list[dict] = []
        listing = _Exec.run(ctx, "ls /sys/class/backlight/ 2>/dev/null")
        if not listing.ok or not listing.stdout.strip():
            return out

        for name in listing.lines():
            brightness = _Exec.run(
                ctx, f"cat /sys/class/backlight/{name}/brightness 2>/dev/null"
            ).int_(0)
            max_brightness = _Exec.run(
                ctx, f"cat /sys/class/backlight/{name}/max_brightness 2>/dev/null"
            ).int_(255)
            bl_power = _Exec.run(
                ctx, f"cat /sys/class/backlight/{name}/bl_power 2>/dev/null"
            ).int_(0)
            display_name = _Exec.run(
                ctx, f"cat /sys/class/backlight/{name}/display_name 2>/dev/null"
            ).text("") or None

            out.append({
                "name": name,
                "brightness": brightness,
                "max_brightness": max_brightness,
                "bl_power": bl_power,
                "display_name": display_name,
                "sysfs_path": f"/sys/class/backlight/{name}",
            })
        return out

    def _probe_framebuffers(self, ctx: ProbeContext) -> list[str]:
        r = _Exec.run(ctx, "ls /dev/fb* 2>/dev/null")
        return r.lines() if r.ok else []

    def _probe_i2c_buses(self, ctx: ProbeContext) -> list[dict]:
        buses: list[dict] = []
        r = _Exec.run(ctx, "ls /dev/i2c-* 2>/dev/null")
        if not r.ok or not r.stdout.strip():
            return buses

        has_i2cdetect = _Exec.run(ctx, "which i2cdetect 2>/dev/null").ok

        for entry in r.lines():
            m = re.search(r"i2c-(\d+)", entry)
            if not m:
                continue
            bus_num = int(m.group(1))
            devices: list[str] = []

            if has_i2cdetect:
                scan = _Exec.run(ctx, f"i2cdetect -y {bus_num} 2>/dev/null")
                if scan.ok:
                    for line in scan.stdout.splitlines():
                        parts = line.split()
                        if not parts or not parts[0].endswith(":"):
                            continue
                        try:
                            row_base = int(parts[0].rstrip(":"), 16)
                        except ValueError:
                            continue
                        for i, val in enumerate(parts[1:]):
                            if val not in ("--", "UU"):
                                devices.append(f"0x{row_base + i:02x}")

            buses.append({
                "bus": bus_num,
                "devices": devices,
                "sysfs_path": entry,
            })
        return buses

    def _probe_dsi_dmesg(self, ctx: ProbeContext) -> list[str]:
        r = _Exec.run(
            ctx,
            "dmesg 2>/dev/null | grep -iE 'dsi|panel|backlight|waveshare|drm.*rp1' "
            "| grep -v 'cycle\\|bluetooth\\|brcm\\|Broad' | tail -30",
        )
        return r.lines() if r.ok else []

    def _probe_kernel_modules(self, ctx: ProbeContext) -> list[str]:
        pattern = r"vc4|v3d|drm|panel_waveshare|dw_mipi_dsi|gpu_sched|videobuf2|rp1"
        r = _Exec.run(
            ctx,
            f"lsmod 2>/dev/null | awk '{{print $1}}' | grep -Ei '{pattern}'",
        )
        return sorted(set(r.lines())) if r.ok else []

    def _probe_wayland_sockets(self, ctx: ProbeContext) -> list[str]:
        r = _Exec.run(
            ctx, "ls /run/user/$(id -u)/ 2>/dev/null | grep '^wayland-'"
        )
        return r.lines() if r.ok and r.stdout.strip() else []

    def _probe_compositor_processes(self, ctx: ProbeContext) -> dict[str, list[int]]:
        processes = ["labwc", "chromium", "kanshi", "weston", "sway"]
        result: dict[str, list[int]] = {}
        for proc in processes:
            r = _Exec.run(ctx, f"pgrep -d ',' '{proc}' 2>/dev/null")
            if r.ok and r.stdout.strip():
                try:
                    pids = [int(x) for x in r.stdout.strip().split(",") if x.strip()]
                except ValueError:
                    pids = []
                if pids:
                    result[proc] = pids
        return result

    def _check_kms(self, ctx: ProbeContext) -> bool:
        r = _Exec.run(
            ctx,
            "grep -q 'vc4-kms-v3d' /boot/firmware/config.txt 2>/dev/null "
            "&& echo yes || echo no",
        )
        return "yes" in (r.stdout if r.ok else "")

    def _get_kms_driver(self, ctx: ProbeContext) -> str:
        r = _Exec.run(
            ctx, "grep -E 'dtoverlay=vc4' /boot/firmware/config.txt 2>/dev/null"
        )
        if not r.ok or not r.stdout.strip():
            return "unknown"
        for line in r.stdout.splitlines():
            if "vc4" in line and "=" in line:
                return line.split("=", 1)[1].strip()
        return "unknown"
