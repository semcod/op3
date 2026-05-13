"""Port-parity tests for the RPi display diagnostic rule-set.

These tests are the canonical spec for the rules ported from
``redeploy/detect/hardware_rules.py``.  If you add a new rule to
:data:`opstree.probes.builtin.rpi_diagnostics.RPI_DISPLAY_RULES`, add a
test here — do not edit the engine.
"""

from __future__ import annotations

from opstree.probes.builtin.rpi_diagnostics import (
    RPI_DISPLAY_RULES,
    diagnose_display_layer,
)


def _hw(**overrides) -> dict:
    """Build a baseline 'healthy' hardware dict and apply overrides."""
    base = {
        "board_model": "Raspberry Pi 5 Model B Rev 1.0",
        "kernel": "6.6.20+rpt-rpi-v8",
        "config_txt": (
            "dtoverlay=vc4-kms-v3d\n"
            "dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch\n"
            "dtparam=i2c_arm=on\n"
        ),
        "config_txt_path": "/boot/firmware/config.txt",
        "dsi_overlays": ["dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch"],
        "drm_outputs": [
            {
                "name": "card1-DSI-2",
                "connector": "DSI-2",
                "status": "connected",
                "enabled": "enabled",
                "edid_bytes": 128,
                "power_state": "on",
                "sysfs_path": "/sys/class/drm/card1-DSI-2",
                "modes": ["1280x800@60"],
                "transform": "normal",
                "scale": "1.0",
                "position": "0,0",
            }
        ],
        "wlr_outputs": [{"output": "DSI-2", "enabled": True, "mode": "1280x800@60"}],
        "backlights": [
            {
                "name": "11-0045",
                "brightness": 255,
                "max_brightness": 255,
                "bl_power": 0,
                "display_name": "DSI-2",
                "sysfs_path": "/sys/class/backlight/11-0045",
            }
        ],
        "framebuffers": ["/dev/fb0"],
        "i2c_buses": [{"bus": 11, "devices": ["0x45"], "sysfs_path": "/dev/i2c-11"}],
        "dsi_dmesg": [],
        "dsi_dmesg_errors": [],
        "kernel_modules": ["vc4", "drm", "drm_kms_helper", "panel_waveshare_dsi"],
        "wayland_sockets": ["wayland-0"],
        "compositor_processes": {"labwc": [1234], "chromium": [5678]},
        "kms_enabled": True,
        "kms_driver": "vc4-kms-v3d",
    }
    base.update(overrides)
    return base


def _names(diags) -> list[str]:
    return [d.rule_name for d in diags]


def test_healthy_system_emits_only_all_ok():
    diags = diagnose_display_layer(_hw())
    names = _names(diags)
    assert "all_ok" in names
    assert not any(d.severity in ("error", "critical") for d in diags)


def test_no_dsi_overlay_fires_when_overlay_missing():
    hw = _hw(dsi_overlays=[], config_txt="dtoverlay=vc4-kms-v3d\n")
    diags = diagnose_display_layer(hw)
    assert "no_dsi_overlay" in _names(diags)


def test_display_auto_detect_conflict():
    hw = _hw(
        config_txt=(
            "dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch\ndisplay_auto_detect=1\n"
        )
    )
    assert "display_auto_detect_conflict" in _names(diagnose_display_layer(hw))


def test_dsi_overlay_no_drm_connector():
    hw = _hw(drm_outputs=[])
    diags = diagnose_display_layer(hw)
    assert "dsi_overlay_no_drm_connector" in _names(diags)


def test_dsi_no_edid_panel_missing():
    hw = _hw(
        drm_outputs=[
            {
                "name": "card1-DSI-2",
                "connector": "DSI-2",
                "status": "connected",
                "enabled": "enabled",
                "edid_bytes": 0,
                "power_state": "on",
            }
        ]
    )
    assert "dsi_no_edid_panel_missing" in _names(diagnose_display_layer(hw))


def test_dsi_connector_not_connected():
    hw = _hw(
        drm_outputs=[
            {
                "name": "card1-DSI-2",
                "connector": "DSI-2",
                "status": "disconnected",
                "enabled": "enabled",
                "edid_bytes": 128,
                "power_state": "on",
            }
        ]
    )
    diags = diagnose_display_layer(hw)
    assert "dsi_connector_not_connected" in _names(diags)
    match = next(d for d in diags if d.rule_name == "dsi_connector_not_connected")
    assert "disconnected" in match.message


def test_dsi_connected_no_backlight():
    hw = _hw(backlights=[])
    assert "dsi_connected_no_backlight" in _names(diagnose_display_layer(hw))


def test_dsi_backlight_init_failed_extracts_error_code():
    hw = _hw(
        dsi_dmesg_errors=[
            "[  1.234] panel waveshare: failed to enable backlight: -121",
        ]
    )
    diags = diagnose_display_layer(hw)
    match = next(d for d in diags if d.rule_name == "dsi_backlight_init_failed")
    assert "-121" in match.message


def test_no_drm_kernel_driver():
    hw = _hw(kernel_modules=["unrelated_module"])
    assert "no_drm_kernel_driver" in _names(diagnose_display_layer(hw))


def test_dsi_driver_not_loaded():
    hw = _hw(kernel_modules=["vc4", "drm"])  # no dsi/waveshare module
    assert "dsi_driver_not_loaded" in _names(diagnose_display_layer(hw))


def test_i2c_arm_not_enabled():
    hw = _hw(
        config_txt="dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch\n",
        i2c_buses=[],
    )
    assert "i2c_arm_not_enabled" in _names(diagnose_display_layer(hw))


def test_i2c_backlight_bus_empty():
    hw = _hw(
        backlights=[
            {
                "name": "11-0045",
                "brightness": 255,
                "max_brightness": 255,
                "bl_power": 0,
                "display_name": "DSI-2",
                "sysfs_path": "/sys/class/backlight/11-0045",
            }
        ],
        i2c_buses=[{"bus": 11, "devices": [], "sysfs_path": "/dev/i2c-11"}],
    )
    assert "i2c_backlight_bus_empty" in _names(diagnose_display_layer(hw))


def test_compositor_not_running():
    hw = _hw(compositor_processes={"kanshi": [1]})
    assert "compositor_not_running" in _names(diagnose_display_layer(hw))


def test_wayland_socket_missing():
    hw = _hw(wayland_sockets=[])
    assert "wayland_socket_missing" in _names(diagnose_display_layer(hw))


def test_chromium_not_running_info_only():
    hw = _hw(compositor_processes={"labwc": [1]})
    diags = diagnose_display_layer(hw)
    match = next(d for d in diags if d.rule_name == "chromium_not_running")
    assert match.severity == "info"


def test_dpms_off():
    hw = _hw(
        drm_outputs=[
            {
                "name": "card1-DSI-2",
                "connector": "DSI-2",
                "status": "connected",
                "enabled": "enabled",
                "edid_bytes": 128,
                "power_state": "off",
                "sysfs_path": "/sys/class/drm/card1-DSI-2",
            }
        ]
    )
    diags = diagnose_display_layer(hw)
    match = next(d for d in diags if d.rule_name == "dpms_off")
    assert "DPMS OFF" in match.message


def test_no_wayland_output():
    hw = _hw(wlr_outputs=[])
    assert "no_wayland_output" in _names(diagnose_display_layer(hw))


def test_all_ok_no_wayland():
    hw = _hw(wlr_outputs=[])
    assert "all_ok_no_wayland" in _names(diagnose_display_layer(hw))


def test_backlight_power_off_dynamic_rule():
    hw = _hw(
        backlights=[
            {
                "name": "11-0045",
                "brightness": 255,
                "max_brightness": 255,
                "bl_power": 4,
                "display_name": "DSI-2",
                "sysfs_path": "/sys/class/backlight/11-0045",
            }
        ]
    )
    diags = diagnose_display_layer(hw)
    match = next(d for d in diags if d.rule_name == "backlight_power_off")
    assert "power is OFF" in match.message
    assert "11-0045" in match.fix


def test_backlight_brightness_zero_dynamic_rule():
    hw = _hw(
        backlights=[
            {
                "name": "11-0045",
                "brightness": 0,
                "max_brightness": 255,
                "bl_power": 0,
                "display_name": "DSI-2",
                "sysfs_path": "/sys/class/backlight/11-0045",
            }
        ]
    )
    diags = diagnose_display_layer(hw)
    assert "backlight_brightness_zero" in _names(diags)


def test_i2c_chip_missing_dynamic_rule():
    hw = _hw(
        backlights=[
            {
                "name": "11-0045",
                "brightness": 255,
                "max_brightness": 255,
                "bl_power": 0,
                "display_name": "DSI-2",
                "sysfs_path": "/sys/class/backlight/11-0045",
            }
        ],
        i2c_buses=[{"bus": 11, "devices": ["0x50"], "sysfs_path": "/dev/i2c-11"}],
    )
    diags = diagnose_display_layer(hw)
    match = next(d for d in diags if d.rule_name == "i2c_chip_missing")
    assert "0x45" in match.message


def test_rule_names_are_unique():
    # Dynamic rules do emit diagnostics that reuse rule_name, but the
    # Rule objects themselves must have unique names so authors can
    # reference them by exclusion, exclude lists, etc.
    names = [r.name for r in RPI_DISPLAY_RULES]
    assert len(names) == len(set(names)), f"duplicate rule names: {names}"
