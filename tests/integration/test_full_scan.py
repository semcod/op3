"""Integration test with mock context for full scan."""

from opstree.layers.tree import LayerTree
from opstree.layers.builtin import PhysicalLayer, OsLayer, RuntimeLayer
from opstree.probes.context import MockContext, ExecuteResult
from opstree.probes.builtin.physical_rpi import RpiPhysicalDisplayProbe
from opstree.probes.builtin.os_linux import OsKernelProbe, OsConfigProbe
from opstree.probes.builtin.runtime_container import RuntimeContainerProbe
from opstree.scanner.linear import LinearScanner
from opstree.probes.registry import ProbeRegistry


def test_full_scan_with_mock_context():
    """Test full scan with mocked SSH context."""
    # Setup mock responses
    mock_responses = {
        # RPi detection
        "test -f /sys/firmware/devicetree/base/model && cat /sys/firmware/devicetree/base/model": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        # Board model
        "cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\\0'": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        # DRM outputs
        "ls /sys/class/drm/ 2>/dev/null": ExecuteResult(
            "card0-DSI-1\ncard1-HDMI-A-1", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/status 2>/dev/null": ExecuteResult(
            "connected", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/enabled 2>/dev/null": ExecuteResult(
            "enabled", "", 0
        ),
        "wc -c < /sys/class/drm/card0-DSI-1/edid 2>/dev/null": ExecuteResult(
            "0", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/dpms 2>/dev/null": ExecuteResult("On", "", 0),
        "cat /sys/class/drm/card1-HDMI-A-1/status 2>/dev/null": ExecuteResult(
            "connected", "", 0
        ),
        "cat /sys/class/drm/card1-HDMI-A-1/enabled 2>/dev/null": ExecuteResult(
            "enabled", "", 0
        ),
        "wc -c < /sys/class/drm/card1-HDMI-A-1/edid 2>/dev/null": ExecuteResult(
            "128", "", 0
        ),
        "cat /sys/class/drm/card1-HDMI-A-1/dpms 2>/dev/null": ExecuteResult(
            "On", "", 0
        ),
        # Backlights
        "ls /sys/class/backlight/ 2>/dev/null": ExecuteResult(
            "raspberrypi-touchscreen", "", 0
        ),
        "cat /sys/class/backlight/raspberrypi-touchscreen/brightness 2>/dev/null": ExecuteResult(
            "255", "", 0
        ),
        "cat /sys/class/backlight/raspberrypi-touchscreen/max_brightness 2>/dev/null": ExecuteResult(
            "255", "", 0
        ),
        # KMS
        "grep -q 'vc4-kms-v3d' /boot/firmware/config.txt 2>/dev/null && echo yes || echo no": ExecuteResult(
            "yes", "", 0
        ),
        "grep -E 'dtoverlay=vc4' /boot/firmware/config.txt 2>/dev/null": ExecuteResult(
            "dtoverlay=vc4-kms-v3d", "", 0
        ),
        # Kernel
        "uname -s": ExecuteResult("Linux", "", 0),
        "uname -r": ExecuteResult("6.6.20+rpt-rpi-v8", "", 0),
        "uname -m": ExecuteResult("aarch64", "", 0),
        "hostname": ExecuteResult("pi5-kiosk", "", 0),
        "cat /proc/uptime": ExecuteResult("345678.12 1234567.89", "", 0),
        # Config
        "cat /boot/firmware/config.txt 2>/dev/null": ExecuteResult(
            "dtoverlay=vc4-kms-v3d\nmax_framebuffers=2", "", 0
        ),
        "cat /proc/cmdline 2>/dev/null": ExecuteResult(
            "console=serial0,115200 console=tty1 root=PARTUUID=...", "", 0
        ),
        # Containers
        "which podman": ExecuteResult("/usr/bin/podman", "", 0),
        "podman --version 2>/dev/null": ExecuteResult("podman version 4.4.4", "", 0),
        "podman ps -a --format json 2>/dev/null": ExecuteResult(
            '[{"Id":"abc123def456","Names":["kiosk-browser"],"Image":"localhost/kiosk-browser:latest","State":"running","Status":"Up 2 hours","Labels":{"io.podman.annotations.restartpolicy":"always"}}]',
            "",
            0,
        ),
    }

    # Create mock context
    ctx = MockContext(responses=mock_responses)

    # Register probes
    registry = ProbeRegistry()
    registry.register(RpiPhysicalDisplayProbe())
    registry.register(OsKernelProbe())
    registry.register(OsConfigProbe())
    registry.register(RuntimeContainerProbe())

    # Create layer tree
    tree = LayerTree()
    tree.register(PhysicalLayer.display)
    tree.register(PhysicalLayer.compute)  # Add dependency for kernel
    tree.register(OsLayer.kernel)
    tree.register(OsLayer.config)
    tree.register(RuntimeLayer.container)

    # Scan
    scanner = LinearScanner(tree)
    scanner.probe_registry = registry
    snapshot = scanner.scan("mock", ctx.execute)

    # Assertions
    assert snapshot.target == "mock"
    assert len(snapshot.layers) > 0

    # Check physical display layer
    if "physical.display" in snapshot.layers:
        display_data = snapshot.layers["physical.display"].data
        assert display_data["board_model"] == "Raspberry Pi 5 Model B Rev 1.0"
        assert len(display_data["drm_outputs"]) == 2
        assert display_data["kms_enabled"] == True

    # Check OS kernel layer
    if "os.kernel" in snapshot.layers:
        kernel_data = snapshot.layers["os.kernel"].data
        assert kernel_data["version"] == "6.6.20+rpt-rpi-v8"
        assert kernel_data["arch"] == "aarch64"
        assert kernel_data["hostname"] == "pi5-kiosk"

    # Check runtime container layer
    if "runtime.container" in snapshot.layers:
        container_data = snapshot.layers["runtime.container"].data
        assert container_data["runtime"] == "podman"
        assert container_data["version"] == "4.4.4"
        assert len(container_data["containers"]) == 1
        assert container_data["containers"][0]["name"] == "kiosk-browser"


def test_rpi_probe_anomaly_detection():
    """Test that RPi probe detects DSI+HDMI anomaly."""
    mock_responses = {
        "test -f /sys/firmware/devicetree/base/model && cat /sys/firmware/devicetree/base/model": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        "cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\\0'": ExecuteResult(
            "Raspberry Pi 5 Model B Rev 1.0", "", 0
        ),
        "ls /sys/class/drm/ 2>/dev/null": ExecuteResult(
            "card0-DSI-1\ncard1-HDMI-A-1", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/status 2>/dev/null": ExecuteResult(
            "connected", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/enabled 2>/dev/null": ExecuteResult(
            "enabled", "", 0
        ),
        "wc -c < /sys/class/drm/card0-DSI-1/edid 2>/dev/null": ExecuteResult(
            "0", "", 0
        ),
        "cat /sys/class/drm/card0-DSI-1/dpms 2>/dev/null": ExecuteResult("On", "", 0),
        "cat /sys/class/drm/card1-HDMI-A-1/status 2>/dev/null": ExecuteResult(
            "connected", "", 0
        ),
        "cat /sys/class/drm/card1-HDMI-A-1/enabled 2>/dev/null": ExecuteResult(
            "enabled", "", 0
        ),
        "wc -c < /sys/class/drm/card1-HDMI-A-1/edid 2>/dev/null": ExecuteResult(
            "128", "", 0
        ),
        "cat /sys/class/drm/card1-HDMI-A-1/dpms 2>/dev/null": ExecuteResult(
            "On", "", 0
        ),
        "ls /sys/class/backlight/ 2>/dev/null": ExecuteResult("", "", 0),
        "grep -q 'vc4-kms-v3d' /boot/firmware/config.txt 2>/dev/null && echo yes || echo no": ExecuteResult(
            "yes", "", 0
        ),
        "grep -E 'dtoverlay=vc4' /boot/firmware/config.txt 2>/dev/null": ExecuteResult(
            "dtoverlay=vc4-kms-v3d", "", 0
        ),
    }

    ctx = MockContext(responses=mock_responses)
    probe = RpiPhysicalDisplayProbe()

    result = probe.scan(ctx)
    anomalies = probe.anomalies(result.layer_data)

    # Should detect anomaly with both DSI and HDMI connected
    assert len(anomalies) > 0
    assert anomalies[0]["severity"] == "warning"
    assert "output routing ambiguous" in anomalies[0]["message"]
