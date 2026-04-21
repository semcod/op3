"""Probe dla systemu operacyjnego Linux — kernel, systemd, config."""
from __future__ import annotations
from datetime import datetime, timezone
from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class OsKernelProbe:
    """Skanuje jądro Linux."""
    layer_id = "os.kernel"
    probe_name = "os_linux"
    
    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        result = ctx.execute("uname -s")
        if hasattr(result, 'ok'):
            return result.ok and "Linux" in result.stdout
        stdout, _, rc = result
        return rc == 0 and "Linux" in stdout
    
    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        data = {
            "version": self._get_kernel_version(ctx),
            "arch": self._get_arch(ctx),
            "hostname": self._get_hostname(ctx),
            "uptime_seconds": self._get_uptime(ctx),
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
    
    def _get_kernel_version(self, ctx: ProbeContext) -> str:
        result = ctx.execute("uname -r")
        if hasattr(result, 'ok'):
            return result.stdout.strip() if result.ok else "unknown"
        stdout, _, rc = result
        return stdout.strip() if rc == 0 else "unknown"
    
    def _get_arch(self, ctx: ProbeContext) -> str:
        result = ctx.execute("uname -m")
        if hasattr(result, 'ok'):
            return result.stdout.strip() if result.ok else "unknown"
        stdout, _, rc = result
        return stdout.strip() if rc == 0 else "unknown"
    
    def _get_hostname(self, ctx: ProbeContext) -> str:
        result = ctx.execute("hostname")
        if hasattr(result, 'ok'):
            return result.stdout.strip() if result.ok else "unknown"
        stdout, _, rc = result
        return stdout.strip() if rc == 0 else "unknown"
    
    def _get_uptime(self, ctx: ProbeContext) -> int:
        result = ctx.execute("cat /proc/uptime")
        if hasattr(result, 'ok'):
            if result.ok:
                try:
                    uptime_seconds = float(result.stdout.strip().split()[0])
                    return int(uptime_seconds)
                except (ValueError, IndexError):
                    pass
            return 0
        stdout, _, rc = result
        if rc == 0:
            try:
                uptime_seconds = float(stdout.strip().split()[0])
                return int(uptime_seconds)
            except (ValueError, IndexError):
                pass
        return 0
    
    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w kernelu."""
        return []


class OsConfigProbe:
    """Skanuje konfigurację systemu."""
    layer_id = "os.config"
    probe_name = "os_config"
    
    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        result = ctx.execute("uname -s")
        if hasattr(result, 'ok'):
            return result.ok and "Linux" in result.stdout
        stdout, _, rc = result
        return rc == 0 and "Linux" in stdout
    
    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        config_txt_path, config_txt = self._read_config_txt(ctx)
        cmdline = self._read_cmdline(ctx)
        
        data = {
            "config_txt": config_txt,
            "config_txt_path": config_txt_path,
            "cmdline": cmdline,
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
    
    def _read_config_txt(self, ctx: ProbeContext) -> tuple[str, str]:
        """Read /boot/firmware/config.txt (RPi5) or /boot/config.txt."""
        for path in ("/boot/firmware/config.txt", "/boot/config.txt"):
            result = ctx.execute(f"cat {path} 2>/dev/null")
            if hasattr(result, 'ok'):
                if result.ok and result.stdout.strip():
                    return path, result.stdout
            else:
                stdout, _, rc = result
                if rc == 0 and stdout.strip():
                    return path, stdout
        return "/boot/firmware/config.txt", ""
    
    def _read_cmdline(self, ctx: ProbeContext) -> str:
        """Read /proc/cmdline."""
        result = ctx.execute("cat /proc/cmdline 2>/dev/null")
        if hasattr(result, 'ok'):
            return result.stdout if result.ok else ""
        stdout, _, rc = result
        return stdout if rc == 0 else ""
    
    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w konfiguracji."""
        return []
