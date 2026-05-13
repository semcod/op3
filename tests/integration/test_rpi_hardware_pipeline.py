"""End-to-end: MockContext → RpiPhysicalDisplayProbe → RPI_DISPLAY_RULES."""

from __future__ import annotations

from opstree.probes.builtin.physical_rpi import RpiPhysicalDisplayProbe
from opstree.probes.builtin.rpi_diagnostics import diagnose_display_layer
from opstree.probes.context import ExecuteResult, MockContext


def _common_responses(extra: dict | None = None) -> dict:
    responses = {
        "test -f /sys/firmware/devicetree/base/model && "
        "cat /sys/firmware/devicetree/base/model": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        "cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\\0'": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        "uname -r": ExecuteResult("6.6.20+rpt-rpi-v8", "", 0),
        "cat /boot/firmware/config.txt 2>/dev/null": ExecuteResult(
            "dtoverlay=vc4-kms-v3d\n"
            "dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch\n"
            "dtparam=i2c_arm=on\n",
            "",
            0,
        ),
        "cat /boot/config.txt 2>/dev/null": ExecuteResult("", "", 1),
        "ls /sys/class/drm/ 2>/dev/null": ExecuteResult("card1-DSI-2", "", 0),
        "cat /sys/class/drm/card1-DSI-2/status 2>/dev/null": ExecuteResult(
            "connected", "", 0
        ),
        "cat /sys/class/drm/card1-DSI-2/enabled 2>/dev/null": ExecuteResult(
            "enabled", "", 0
        ),
        "wc -c < /sys/class/drm/card1-DSI-2/edid 2>/dev/null": ExecuteResult(
            "128", "", 0
        ),
        "cat /sys/class/drm/card1-DSI-2/dpms 2>/dev/null": ExecuteResult("On", "", 0),
        "WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/$(id -u) wlr-randr 2>/dev/null": ExecuteResult(
            'DSI-2 "Waveshare"\n'
            "  Enabled: yes\n"
            "  Modes:\n"
            "    1280x800 px, 60.000000 Hz (preferred, current)\n"
            "  Transform: normal\n"
            "  Scale: 1.000000\n",
            "",
            0,
        ),
        "ls /sys/class/backlight/ 2>/dev/null": ExecuteResult("11-0045", "", 0),
        "cat /sys/class/backlight/11-0045/brightness 2>/dev/null": ExecuteResult(
            "255", "", 0
        ),
        "cat /sys/class/backlight/11-0045/max_brightness 2>/dev/null": ExecuteResult(
            "255", "", 0
        ),
        "cat /sys/class/backlight/11-0045/bl_power 2>/dev/null": ExecuteResult(
            "0", "", 0
        ),
        "cat /sys/class/backlight/11-0045/display_name 2>/dev/null": ExecuteResult(
            "DSI-2", "", 0
        ),
        "ls /dev/fb* 2>/dev/null": ExecuteResult("/dev/fb0", "", 0),
        "ls /dev/i2c-* 2>/dev/null": ExecuteResult("/dev/i2c-1\n/dev/i2c-11", "", 0),
        "which i2cdetect 2>/dev/null": ExecuteResult("/usr/sbin/i2cdetect", "", 0),
        "i2cdetect -y 1 2>/dev/null": ExecuteResult(
            "     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n"
            "00:          -- -- -- -- -- -- -- -- -- -- -- -- --\n",
            "",
            0,
        ),
        "i2cdetect -y 11 2>/dev/null": ExecuteResult(
            "     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f\n"
            "40: -- -- -- -- -- 45 -- -- -- -- -- -- -- -- -- --\n",
            "",
            0,
        ),
        "dmesg 2>/dev/null | grep -iE 'dsi|panel|backlight|waveshare|drm.*rp1' "
        "| grep -v 'cycle\\|bluetooth\\|brcm\\|Broad' | tail -30": ExecuteResult(
            "", "", 0
        ),
        "lsmod 2>/dev/null | awk '{print $1}' "
        "| grep -Ei 'vc4|v3d|drm|panel_waveshare|dw_mipi_dsi|gpu_sched|videobuf2|rp1'": ExecuteResult(
            "vc4\ndrm\ndrm_kms_helper\npanel_waveshare_dsi\n", "", 0
        ),
        "ls /run/user/$(id -u)/ 2>/dev/null | grep '^wayland-'": ExecuteResult(
            "wayland-0", "", 0
        ),
        "pgrep -d ',' 'labwc' 2>/dev/null": ExecuteResult("1234", "", 0),
        "pgrep -d ',' 'chromium' 2>/dev/null": ExecuteResult("5678", "", 0),
        "pgrep -d ',' 'kanshi' 2>/dev/null": ExecuteResult("", "", 1),
        "pgrep -d ',' 'weston' 2>/dev/null": ExecuteResult("", "", 1),
        "pgrep -d ',' 'sway' 2>/dev/null": ExecuteResult("", "", 1),
        "grep -q 'vc4-kms-v3d' /boot/firmware/config.txt 2>/dev/null && echo yes || echo no": ExecuteResult(
            "yes", "", 0
        ),
        "grep -E 'dtoverlay=vc4' /boot/firmware/config.txt 2>/dev/null": ExecuteResult(
            "dtoverlay=vc4-kms-v3d\ndtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch",
            "",
            0,
        ),
        "WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/$(id -u) wlr-randr 2>/dev/null": ExecuteResult(
            "", "", 1
        ),
    }
    if extra:
        responses.update(extra)
    return responses


def test_probe_emits_full_hardware_dict():
    ctx = MockContext(responses=_common_responses())
    probe = RpiPhysicalDisplayProbe()

    assert probe.can_probe(ctx)
    result = probe.scan(ctx)
    data = result.layer_data.data

    assert data["board_model"] == "Raspberry Pi 5 Model B Rev 1.0"
    assert data["kernel"] == "6.6.20+rpt-rpi-v8"
    assert "dtoverlay=vc4-kms-v3d" in data["config_txt"]
    assert data["dsi_overlays"] == ["dtoverlay=vc4-kms-dsi-waveshare-panel,8_0_inch"]
    assert len(data["drm_outputs"]) == 1
    assert data["drm_outputs"][0]["connector"] == "DSI-2"
    assert data["drm_outputs"][0]["modes"] == ["1280x800@60"]
    assert data["wlr_outputs"][0]["output"] == "DSI-2"
    assert data["backlights"][0]["name"] == "11-0045"
    assert data["framebuffers"] == ["/dev/fb0"]
    assert any(b["bus"] == 11 and "0x45" in b["devices"] for b in data["i2c_buses"])
    assert "panel_waveshare_dsi" in data["kernel_modules"]
    assert data["wayland_sockets"] == ["wayland-0"]
    assert data["compositor_processes"] == {"labwc": [1234], "chromium": [5678]}
    assert data["kms_enabled"] is True
    assert "vc4-kms-v3d" in data["kms_driver"]


def test_probe_output_feeds_diagnostics_to_clean_system():
    ctx = MockContext(responses=_common_responses())
    result = RpiPhysicalDisplayProbe().scan(ctx)
    diags = diagnose_display_layer(result.layer_data.data)
    names = [d.rule_name for d in diags]
    assert "all_ok" in names
    assert not any(d.severity in ("error", "critical") for d in diags)


def test_probe_output_feeds_diagnostics_to_broken_system():
    """Simulate a broken rig and verify the right rules fire end-to-end."""
    responses = _common_responses(
        {
            "wc -c < /sys/class/drm/card1-DSI-2/edid 2>/dev/null": ExecuteResult(
                "0", "", 0
            ),
            "ls /sys/class/backlight/ 2>/dev/null": ExecuteResult("", "", 0),
        }
    )
    ctx = MockContext(responses=responses)
    result = RpiPhysicalDisplayProbe().scan(ctx)
    diags = diagnose_display_layer(result.layer_data.data)
    names = {d.rule_name for d in diags}
    # Empty EDID + connected → panel missing
    assert "dsi_no_edid_panel_missing" in names
    # Connected DSI but no backlight sysfs
    assert "dsi_connected_no_backlight" in names
    # Clean-system rule should not fire
    assert "all_ok" not in names
