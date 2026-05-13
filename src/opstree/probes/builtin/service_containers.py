"""Probe dla warstwy service.containers — systemd services."""

from __future__ import annotations
from datetime import datetime, timezone
from opstree.probes.base import ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class ServiceContainersProbe:
    """Skanuje systemd services."""

    layer_id = "service.containers"
    probe_name = "service_containers"

    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        result = ctx.execute("which systemctl")
        if hasattr(result, "ok"):
            return result.ok
        _, _, rc = result
        return rc == 0

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        services = self._list_systemd_services(ctx)

        data = {
            "systemd_services": services,
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

    def _list_systemd_services(self, ctx: ProbeContext) -> list[dict]:
        """Lista systemd services."""
        services = []

        def _exec(cmd: str) -> tuple[str, int]:
            result = ctx.execute(cmd)
            if hasattr(result, "ok"):
                return result.stdout, 0 if result.ok else 1
            return result[0], result[2]

        # Try systemctl list-units --type=service --all
        stdout, rc = _exec(
            "systemctl list-units --type=service --all --no-legend 2>/dev/null"
        )
        if rc == 0:
            for line in stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    service_name = parts[0]
                    load_state = parts[1]
                    active_state = parts[2]
                    sub_state = parts[3]

                    services.append(
                        {
                            "name": service_name,
                            "load": load_state,
                            "active": active_state,
                            "sub": sub_state,
                            "enabled": self._is_service_enabled(ctx, service_name),
                        }
                    )

        return services

    def _is_service_enabled(self, ctx: ProbeContext, service_name: str) -> bool:
        """Sprawdź czy service jest enabled."""
        result = ctx.execute(f"systemctl is-enabled {service_name} 2>/dev/null")
        if hasattr(result, "ok"):
            return "enabled" in result.stdout.lower()
        stdout, _, rc = result
        return rc == 0 and "enabled" in stdout.lower()

    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w services."""
        anomalies = []
        services = data.data.get("systemd_services", [])

        # Check for failed services
        for svc in services:
            if svc.get("active") == "failed":
                anomalies.append(
                    {
                        "severity": "error",
                        "layer": self.layer_id,
                        "message": f"Service {svc.get('name')} is in failed state",
                        "evidence": {"service": svc},
                    }
                )

        return anomalies
