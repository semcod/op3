"""Probe dla warstwy business.health — application health checks."""
from __future__ import annotations
from datetime import datetime, timezone
from opstree.probes.base import Probe, ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class BusinessHealthProbe:
    """Skanuje zdrowie aplikacji."""
    layer_id = "business.health"
    probe_name = "business_health"
    
    def __init__(self, app_name: str = "unknown", health_url: str = None):
        """
        Args:
            app_name: Nazwa aplikacji
            health_url: URL endpointu health check (opcjonalne)
        """
        self.app_name = app_name
        self.health_url = health_url
    
    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        return True  # Always can probe (can report unknown health)
    
    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        health_status = "unknown"
        alerts = []
        
        if self.health_url:
            health_status, alerts = self._check_health_endpoint(ctx, self.health_url)
        
        data = {
            "app_name": self.app_name,
            "app_version": "unknown",  # Could be detected from running containers
            "overall_health": health_status,
            "alerts": alerts,
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
    
    def _check_health_endpoint(self, ctx: ProbeContext, url: str) -> tuple[str, list]:
        """Sprawdź endpoint health."""
        def _exec(cmd: str) -> tuple[str, int]:
            result = ctx.execute(cmd)
            if hasattr(result, 'ok'):
                return result.stdout, 0 if result.ok else 1
            return result[0], result[2]
        
        # Use curl to check health endpoint
        stdout, rc = _exec(f"curl -s -o /dev/null -w '%{{http_code}}' {url} 2>/dev/null")
        
        try:
            status_code = int(stdout.strip()) if rc == 0 else None
        except ValueError:
            status_code = None
        
        if status_code is None:
            return "unknown", [{"severity": "error", "message": f"Failed to reach health endpoint {url}"}]
        
        if 200 <= status_code < 300:
            return "healthy", []
        elif 500 <= status_code < 600:
            return "unhealthy", [{"severity": "error", "message": f"Health check failed with status {status_code}"}]
        else:
            return "degraded", [{"severity": "warning", "message": f"Health check returned status {status_code}"}]
    
    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w zdrowiu aplikacji."""
        anomalies = []
        health = data.data.get("overall_health", "unknown")
        alerts = data.data.get("alerts", [])
        
        if health == "unhealthy":
            anomalies.append({
                "severity": "error",
                "layer": self.layer_id,
                "message": f"Application {data.data.get('app_name')} is unhealthy",
                "evidence": {"health": health, "alerts": alerts},
            })
        elif health == "degraded":
            anomalies.append({
                "severity": "warning",
                "layer": self.layer_id,
                "message": f"Application {data.data.get('app_name')} is degraded",
                "evidence": {"health": health, "alerts": alerts},
            })
        
        return anomalies
