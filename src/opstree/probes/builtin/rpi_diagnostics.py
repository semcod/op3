"""Declarative diagnostic rules for the Raspberry Pi display stack.

Ported from ``redeploy/detect/hardware_rules.py`` so that both
``redeploy`` and any future op3 consumer (``doql``, ad-hoc CLI, etc.)
can share the exact same diagnosis logic.

The rules operate on the ``physical.display`` layer payload produced by
:class:`opstree.probes.builtin.physical_rpi.RpiPhysicalDisplayProbe` —
i.e. a plain ``dict`` with the keys documented on that probe.

Usage::

    from opstree.probes.builtin.rpi_diagnostics import (
        RPI_DISPLAY_RULES,
        diagnose_display_layer,
    )
    diagnostics = diagnose_display_layer(snapshot.layer("physical.display").data)

Adding a new rule: append one :class:`Rule` to :data:`RPI_DISPLAY_RULES`.
No other file needs to change.
"""
from __future__ import annotations

import re
from typing import Any, Iterable

from opstree.diagnostics import Diagnostic, Rule, RuleEngine


HardwareData = dict[str, Any]


# ── helpers ───────────────────────────────────────────────────────────

def _dsi_outputs(hw: HardwareData) -> list[dict]:
    return [o for o in hw.get("drm_outputs", []) if "DSI" in o.get("name", "")]


def _has_dsi_overlay(hw: HardwareData) -> bool:
    return any("dsi" in l.lower() for l in hw.get("dsi_overlays", []))


def _dsi_connected(hw: HardwareData) -> bool:
    return any(o.get("status") == "connected" for o in _dsi_outputs(hw))


def _backlights(hw: HardwareData) -> list[dict]:
    return hw.get("backlights", []) or []


def _i2c_buses(hw: HardwareData) -> list[dict]:
    return hw.get("i2c_buses", []) or []


def _kernel_modules(hw: HardwareData) -> list[str]:
    return hw.get("kernel_modules", []) or []


def _backlight_chip_addr(name: str) -> tuple[int, str] | None:
    """Parse '11-0045' → (11, '0x45')."""
    m = re.match(r"^(\d+)-0*([0-9a-f]+)$", name)
    if not m:
        return None
    return int(m.group(1)), f"0x{int(m.group(2), 16):02x}"


def _all_ok(hw: HardwareData) -> bool:
    dsi = _dsi_outputs(hw)
    bls = _backlights(hw)
    return (
        _has_dsi_overlay(hw)
        and bool(dsi)
        and _dsi_connected(hw)
        and bool(bls)
        and all(b.get("bl_power", 0) == 0 and b.get("brightness", 0) > 0 for b in bls)
    )


# ── dynamic (per-device) rules ────────────────────────────────────────

def _backlight_power_off_rules(hw: HardwareData) -> Iterable[Diagnostic]:
    for bl in _backlights(hw):
        name = bl.get("name", "?")
        if bl.get("bl_power", 0) != 0:
            yield Diagnostic(
                component="backlight",
                severity="error",
                rule_name="backlight_power_off",
                message=(
                    f"Backlight {name} power is OFF "
                    f"(bl_power={bl.get('bl_power', 0)})"
                ),
                fix=f"echo 0 | sudo tee /sys/class/backlight/{name}/bl_power",
            )
        if bl.get("brightness", 0) == 0:
            yield Diagnostic(
                component="backlight",
                severity="warning",
                rule_name="backlight_brightness_zero",
                message=f"Backlight {name} brightness is 0",
                fix=f"echo 255 | sudo tee /sys/class/backlight/{name}/brightness",
            )


def _i2c_chip_missing_rules(hw: HardwareData) -> Iterable[Diagnostic]:
    for bl in _backlights(hw):
        parsed = _backlight_chip_addr(bl.get("name", ""))
        if not parsed:
            continue
        bus_num, addr = parsed
        bus = next((b for b in _i2c_buses(hw) if b.get("bus") == bus_num), None)
        if not bus:
            continue
        devices = bus.get("devices") or []
        if devices and addr not in devices:
            yield Diagnostic(
                component="i2c",
                severity="warning",
                rule_name="i2c_chip_missing",
                message=(
                    f"Backlight chip expected at {addr} on i2c-{bus_num} "
                    f"but not found in scan (found: {devices or 'none'})"
                ),
                fix=(
                    "Verify 4-pin header is connected and i2c_arm=on is in config.txt.\n"
                    f"Manual test: i2cdetect -y {bus_num}"
                ),
            )


# ── static rules ──────────────────────────────────────────────────────

_STATIC_RULES: list[Rule[HardwareData]] = [
    Rule(
        name="no_dsi_overlay",
        component="overlay",
        severity="error",
        predicate=lambda hw: not _has_dsi_overlay(hw),
        message="No DSI dtoverlay found in config.txt",
        fix=(
            "Add to /boot/firmware/config.txt:\n"
            "  dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch\n"
            "Then reboot."
        ),
    ),
    Rule(
        name="display_auto_detect_conflict",
        component="overlay",
        severity="warning",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and "display_auto_detect=1" in hw.get("config_txt", "")
        ),
        message="display_auto_detect=1 may conflict with manual DSI overlay",
        fix=(
            "Set display_auto_detect=0 in /boot/firmware/config.txt\n"
            "  sudo sed -i 's/^display_auto_detect=1/display_auto_detect=0/' "
            "/boot/firmware/config.txt"
        ),
    ),
    Rule(
        name="dsi_overlay_no_drm_connector",
        component="dsi",
        severity="error",
        predicate=lambda hw: _has_dsi_overlay(hw) and not _dsi_outputs(hw),
        message="DSI overlay loaded but no DRM DSI connector found in /sys/class/drm/",
        fix=(
            "Check physical connection: For RPi5 the Waveshare 8\" (C) requires:\n"
            "  1. DSI-Cable-12cm → DISP1 (22-pin connector)\n"
            "  2. 4-pin header → RPi GPIO (5V + GND + SDA + SCL)\n"
            "Reseat the FPC ribbon cable and reboot."
        ),
    ),
    Rule(
        name="dsi_no_edid_panel_missing",
        component="dsi",
        severity="error",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and bool(_dsi_outputs(hw))
            and all(o.get("edid_bytes", 0) == 0 for o in _dsi_outputs(hw))
        ),
        message=(
            "DSI panel not physically connected — EDID is empty (0 bytes). "
            "Overlay is loaded but no display detected on the cable."
        ),
        fix=(
            "Connect the DSI display FPC cable to DISP1 (22-pin connector) and reboot.\n"
            "  - Silver contacts face the board\n"
            "  - ZIF latch must be locked\n"
            "  - For RPi5: use DISP1 (lower connector), not DISP0 (upper)"
        ),
    ),
    Rule(
        name="dsi_connector_not_connected",
        component="dsi",
        severity="error",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and bool(_dsi_outputs(hw))
            and not _dsi_connected(hw)
        ),
        message=lambda hw: (
            f"DSI connector status: {_dsi_outputs(hw)[0].get('status', 'unknown')} "
            "(expected: connected)"
        ),
        fix=(
            "Physical connection issue. Check:\n"
            "  1. FPC ribbon seated in DISP1 (22-pin) — not DISP0 (15-pin)\n"
            "  2. ZIF latch locked down firmly on both ends\n"
            "  3. Silver contacts facing correct direction (towards board)"
        ),
    ),
    Rule(
        name="dsi_connected_no_backlight",
        component="backlight",
        severity="error",
        predicate=lambda hw: _dsi_connected(hw) and not _backlights(hw),
        message="DSI connected but no backlight sysfs device found",
        fix=(
            "The 4-pin header connection may be missing or the I2C backlight\n"
            "controller is not initializing. Check:\n"
            "  - 4-pin cable from display board → RPi GPIO header\n"
            "  - Pin 1 (5V), Pin 2 (GND), Pin 3 (SDA=GPIO2), Pin 4 (SCL=GPIO3)\n"
            "  - dtparam=i2c_arm=on must be set in config.txt"
        ),
    ),
    Rule(
        name="dsi_backlight_init_failed",
        component="backlight",
        severity="error",
        predicate=lambda hw: any(
            "failed to enable backlight" in l
            for l in hw.get("dsi_dmesg_errors", [])
        ),
        message=lambda hw: (
            "Backlight controller failed to initialise "
            "(dmesg: 'failed to enable backlight'). "
            "Error code: "
            + next(
                (
                    m.group(1)
                    for l in hw.get("dsi_dmesg_errors", [])
                    if "failed to enable backlight" in l
                    for m in [re.search(r"backlight: (-\d+)", l)]
                    if m
                ),
                "unknown",
            )
            + "\nThis means the I2C backlight chip (usually at 0x45) "
            "is not responding."
        ),
        fix=(
            "1. Check 4-pin header cable (display board ↔ RPi GPIO):\n"
            "     Display pin 1 (5V)  → RPi Pin 2 or 4 (5V)\n"
            "     Display pin 2 (GND) → RPi Pin 6 (GND)\n"
            "     Display pin 3 (SDA) → RPi Pin 3 (GPIO2/SDA1)\n"
            "     Display pin 4 (SCL) → RPi Pin 5 (GPIO3/SCL1)\n"
            "2. Verify dtparam=i2c_arm=on in /boot/firmware/config.txt\n"
            "3. Check I2C scan: i2cdetect -y 1  (expect device at 0x45)\n"
            "4. Error -121 = EREMOTEIO: device not responding on I2C bus"
        ),
    ),
    Rule(
        name="no_drm_kernel_driver",
        component="driver",
        severity="error",
        predicate=lambda hw: (
            bool(_kernel_modules(hw))
            and not any(m in ("vc4", "drm_rp1_dsi", "drm") for m in _kernel_modules(hw))
        ),
        message="DRM/VC4 kernel driver not loaded — display cannot work without it",
        fix=(
            "Check if vc4-kms-v3d overlay is in /boot/firmware/config.txt:\n"
            "  dtoverlay=vc4-kms-v3d\n"
            "Verify loaded modules: lsmod | grep -E 'vc4|drm'\n"
            "If missing, add overlay and reboot."
        ),
    ),
    Rule(
        name="dsi_driver_not_loaded",
        component="driver",
        severity="error",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and bool(_kernel_modules(hw))
            and not any(
                "dsi" in m.lower() or "waveshare" in m.lower()
                for m in _kernel_modules(hw)
            )
        ),
        message=lambda hw: (
            "DSI overlay loaded in config.txt but no DSI kernel module found in lsmod. "
            f"Loaded modules: {', '.join(_kernel_modules(hw)) or 'none'}"
        ),
        fix=(
            "The DSI driver did not load. Check dmesg for module errors:\n"
            "  dmesg | grep -i 'dsi\\|waveshare\\|panel'\n"
            "Possible causes:\n"
            "  - Wrong overlay name (check /boot/firmware/overlays/README)\n"
            "  - Module file missing (check /lib/modules/$(uname -r)/)\n"
            "  - Hardware incompatibility (verify panel variant: "
            "8_0_inch_a vs 8_0_inch_b)"
        ),
    ),
    Rule(
        name="i2c_arm_not_enabled",
        component="i2c",
        severity="warning",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and "dtparam=i2c_arm=on" not in hw.get("config_txt", "")
            and not _i2c_buses(hw)
        ),
        message=(
            "dtparam=i2c_arm=on not found in config.txt — "
            "I2C bus for backlight controller (0x45) may not be available"
        ),
        fix=(
            "Add to /boot/firmware/config.txt:\n"
            "  dtparam=i2c_arm=on\n"
            "Then reboot. Verify: ls /dev/i2c-*"
        ),
    ),
    Rule(
        name="i2c_backlight_bus_empty",
        component="i2c",
        severity="warning",
        predicate=lambda hw: (
            bool(_backlights(hw))
            and any(
                b.get("name", "").startswith("11-")
                or b.get("name", "").startswith("1-")
                for b in _backlights(hw)
            )
            and any(
                b.get("bus") in (1, 11) and not b.get("devices")
                for b in _i2c_buses(hw)
            )
        ),
        message=lambda hw: (
            "Backlight sysfs device exists but I2C scan found no devices "
            "on the backlight bus. Buses scanned: "
            + ", ".join(
                f"i2c-{b['bus']} (0 devices)"
                for b in _i2c_buses(hw)
                if b.get("bus") in (1, 11) and not b.get("devices")
            )
        ),
        fix=(
            "I2C scan returned empty — backlight chip not responding.\n"
            "Check:\n"
            "  i2cdetect -y 1    # expect 0x45 (backlight)\n"
            "  i2cdetect -y 11   # RPi5 DSI I2C bus\n"
            "Verify 4-pin header cable is firmly seated.\n"
            "Check sysfs: cat /sys/class/backlight/*/brightness"
        ),
    ),
    Rule(
        name="compositor_not_running",
        component="compositor",
        severity="warning",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and hw.get("compositor_processes") is not None
            and "labwc" not in (hw.get("compositor_processes") or {})
            and "weston" not in (hw.get("compositor_processes") or {})
            and "sway" not in (hw.get("compositor_processes") or {})
        ),
        message="No Wayland compositor (labwc/weston/sway) detected — kiosk cannot start",
        fix=(
            "Start labwc:\n"
            "  systemctl --user start labwc\n"
            "Or manually: WAYLAND_DISPLAY=wayland-0 labwc &\n"
            "Check autostart: cat ~/.config/labwc/autostart\n"
            "Check service: systemctl --user status labwc"
        ),
    ),
    Rule(
        name="wayland_socket_missing",
        component="compositor",
        severity="warning",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and bool(hw.get("compositor_processes"))
            and not hw.get("wayland_sockets")
        ),
        message=(
            "Wayland socket not found in /run/user/<uid>/ — "
            "compositor may have crashed or not started"
        ),
        fix=(
            "Check: ls /run/user/$(id -u)/wayland-*\n"
            "Check compositor status: systemctl --user status labwc\n"
            "Check logs: journalctl --user -u labwc -n 50\n"
            "XDG_RUNTIME_DIR must point to /run/user/$(id -u)"
        ),
    ),
    Rule(
        name="chromium_not_running",
        component="kiosk",
        severity="info",
        predicate=lambda hw: (
            _has_dsi_overlay(hw)
            and bool(hw.get("compositor_processes"))
            and "labwc" in (hw.get("compositor_processes") or {})
            and "chromium" not in (hw.get("compositor_processes") or {})
        ),
        message="labwc is running but Chromium kiosk is not started",
        fix=(
            "Check kiosk autostart: cat ~/.config/labwc/autostart\n"
            "Check kiosk-launch.sh script\n"
            "Start manually: bash ~/kiosk-launch.sh &"
        ),
    ),
    Rule(
        name="dpms_off",
        component="display",
        severity="warning",
        predicate=lambda hw: any(
            "DSI" in o.get("name", "") and o.get("power_state") == "off"
            for o in hw.get("drm_outputs", [])
        ),
        message=lambda hw: (
            "DSI display is in DPMS OFF state — screen powered down by compositor. "
            "Connector: "
            + next(
                (
                    o.get("sysfs_path") or o.get("name", "?")
                    for o in hw.get("drm_outputs", [])
                    if "DSI" in o.get("name", "") and o.get("power_state") == "off"
                ),
                "?",
            )
        ),
        fix=(
            "Wake the display:\n"
            "  WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u) "
            "wlr-randr --output DSI-2 --on\n"
            "Or disable DPMS in compositor config.\n"
            "Check: cat /sys/class/drm/card1-DSI-2/dpms"
        ),
    ),
    Rule(
        name="no_wayland_output",
        component="compositor",
        severity="warning",
        predicate=lambda hw: (
            bool(_dsi_outputs(hw)) and not hw.get("wlr_outputs")
        ),
        message="wlr-randr returned no outputs — labwc/wayland may not be running",
        fix=(
            "Check: systemctl --user status labwc\n"
            "Start: DISPLAY= labwc &\n"
            "Or check ~/.config/labwc/autostart"
        ),
    ),
    Rule(
        name="all_ok_no_wayland",
        component="compositor",
        severity="warning",
        predicate=lambda hw: _all_ok(hw) and not hw.get("wlr_outputs"),
        message=(
            "Hardware OK but no Wayland output detected. "
            "Blank screen may be labwc/compositor issue."
        ),
        fix=(
            "Try turning the output on explicitly:\n"
            "  WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u) "
            "wlr-randr --output DSI-2 --on\n"
            "Or write test pattern to framebuffer:\n"
            "  dd if=/dev/urandom of=/dev/fb0 bs=1M count=2"
        ),
    ),
]


def _all_ok_rule() -> Rule[HardwareData]:
    """Terminal rule — fires only if everything else is clean."""
    engine_without_me = RuleEngine(_STATIC_RULES)

    def predicate(hw: HardwareData) -> bool:
        if not _all_ok(hw):
            return False
        return not engine_without_me.any_error(
            hw, exclude=("all_ok", "all_ok_no_wayland")
        )

    return Rule(
        name="all_ok",
        component="dsi",
        severity="info",
        predicate=predicate,
        message="DSI display appears correctly configured (connected, backlight on)",
    )


_DYNAMIC_RULES: list[Rule[HardwareData]] = [
    Rule(
        name="backlight_power_off",
        component="backlight",
        dynamic=_backlight_power_off_rules,
    ),
    Rule(
        name="i2c_chip_missing",
        component="i2c",
        dynamic=_i2c_chip_missing_rules,
    ),
]


RPI_DISPLAY_RULES: list[Rule[HardwareData]] = [
    *_STATIC_RULES,
    _all_ok_rule(),
    *_DYNAMIC_RULES,
]


def diagnose_display_layer(layer_data: HardwareData) -> list[Diagnostic]:
    """Run the full RPi display rule-set against a layer data dict."""
    return RuleEngine(RPI_DISPLAY_RULES).evaluate(layer_data)


__all__ = [
    "RPI_DISPLAY_RULES",
    "diagnose_display_layer",
    "HardwareData",
]
