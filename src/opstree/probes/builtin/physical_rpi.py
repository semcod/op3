"""Probe dla fizycznego hardware RPi5 — DSI, DRM, backlight, I2C."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Optional
from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class RpiPhysicalDisplayProbe:
    """Skanuje DSI/HDMI/backlight na Raspberry Pi."""
    layer_id = "physical.display"
    probe_name = "rpi_physical_display"
    
    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        # Sprawdź czy target to RPi
        result = ctx.execute("test -f /sys/firmware/devicetree/base/model && cat /sys/firmware/devicetree/base/model")
        if hasattr(result, 'ok'):
            return result.ok and "Raspberry Pi" in result.stdout
        stdout, _, rc = result
        return rc == 0 and "Raspberry Pi" in stdout
    
    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        data = {
            "board_model": self._probe_board_model(ctx),
            "drm_outputs": self._scan_drm(ctx),
            "backlights": self._scan_backlights(ctx),
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
    
    def _probe_board_model(self, ctx: ProbeContext) -> str:
        """Pobierz model płyty."""
        result = ctx.execute("cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\\0'")
        if hasattr(result, 'ok'):
            return result.stdout.strip() if result.ok else "unknown"
        stdout, _, rc = result
        return stdout.strip() if rc == 0 else "unknown"
    
    def _scan_drm(self, ctx: ProbeContext) -> list[dict]:
        """Skanuj wyjścia DRM."""
        outputs = []
        result = ctx.execute("ls /sys/class/drm/ 2>/dev/null")
        if hasattr(result, 'ok'):
            if not result.ok:
                return outputs
            stdout = result.stdout
        else:
            stdout, _, rc = result
            if not rc == 0:
                return outputs
        
        def _get_stdout(r):
            if hasattr(r, 'ok'):
                return r.stdout.strip() if r.ok else "unknown"
            return r[0].strip() if r[1] == 0 else "unknown"
        
        def _get_int(r):
            if hasattr(r, 'ok'):
                return int(r.stdout.strip()) if r.ok else 0
            try:
                return int(r[0].strip()) if r[1] == 0 else 0
            except (ValueError, IndexError):
                return 0
        
        for entry in stdout.strip().splitlines():
            # Only connector entries like card1-DSI-2, card2-HDMI-A-1
            if not re.match(r'^card\d+-.+', entry):
                continue
            # Extract connector name after first dash+digit
            m = re.match(r'^(card\d+)-(.*)', entry)
            if not m:
                continue
            connector = m.group(2)
            
            status_r = ctx.execute(f"cat /sys/class/drm/{entry}/status 2>/dev/null")
            enabled_r = ctx.execute(f"cat /sys/class/drm/{entry}/enabled 2>/dev/null")
            edid_r = ctx.execute(f"wc -c < /sys/class/drm/{entry}/edid 2>/dev/null")
            dpms_r = ctx.execute(f"cat /sys/class/drm/{entry}/dpms 2>/dev/null")
            
            edid_bytes = _get_int(edid_r)
            
            outputs.append({
                "name": entry,
                "connector": connector,
                "status": _get_stdout(status_r),
                "enabled": _get_stdout(enabled_r),
                "edid_bytes": edid_bytes,
                "dpms": _get_stdout(dpms_r),
            })
        
        return outputs
    
    def _scan_backlights(self, ctx: ProbeContext) -> list[dict]:
        """Skanuj podświetlenia."""
        backlights = []
        result = ctx.execute("ls /sys/class/backlight/ 2>/dev/null")
        if hasattr(result, 'ok'):
            if not result.ok:
                return backlights
            stdout = result.stdout
        else:
            stdout, _, rc = result
            if not rc == 0:
                return backlights
        
        def _get_int(r):
            if hasattr(r, 'ok'):
                return int(r.stdout.strip()) if r.ok else 0
            try:
                return int(r[0].strip()) if r[1] == 0 else 0
            except (ValueError, IndexError, AttributeError):
                return 0
        
        for entry in stdout.strip().splitlines():
            brightness_r = ctx.execute(f"cat /sys/class/backlight/{entry}/brightness 2>/dev/null")
            max_brightness_r = ctx.execute(f"cat /sys/class/backlight/{entry}/max_brightness 2>/dev/null")
            
            brightness = _get_int(brightness_r)
            max_brightness = _get_int(max_brightness_r)
            
            backlights.append({
                "name": entry,
                "brightness": brightness,
                "max_brightness": max_brightness,
            })
        
        return backlights
    
    def _check_kms(self, ctx: ProbeContext) -> bool:
        """Sprawdź czy KMS jest włączony."""
        result = ctx.execute("grep -q 'vc4-kms-v3d' /boot/firmware/config.txt 2>/dev/null && echo yes || echo no")
        if hasattr(result, 'ok'):
            return "yes" in result.stdout
        stdout, _, rc = result
        return "yes" in stdout
    
    def _get_kms_driver(self, ctx: ProbeContext) -> str:
        """Pobierz nazwę sterownika KMS."""
        result = ctx.execute("grep -E 'dtoverlay=vc4' /boot/firmware/config.txt 2>/dev/null")
        if hasattr(result, 'ok'):
            stdout = result.stdout if result.ok else ""
        else:
            stdout, _, rc = result
            if not rc == 0:
                stdout = ""
        
        if stdout:
            for line in stdout.splitlines():
                if "vc4" in line:
                    return line.split("=")[1].strip()
        return "unknown"
    
    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie charakterystyczne dla DSI/HDMI."""
        anomalies = []
        outputs = data.data.get("drm_outputs", [])
        connected = [o for o in outputs if o["status"] == "connected"]
        
        # Anomalia z sesji 109: dwa wyświetlacze connected → Chromium może trafić na zły
        if len(connected) > 1:
            dsi = [o for o in connected if o["name"].startswith("card0-DSI") or "DSI" in o["name"]]
            hdmi = [o for o in connected if "HDMI" in o["name"]]
            if dsi and hdmi:
                anomalies.append({
                    "severity": "warning",
                    "layer": self.layer_id,
                    "message": "Both DSI and HDMI displays connected — output routing ambiguous",
                    "evidence": {"connected_outputs": [o["name"] for o in connected]},
                })
        
        return anomalies
