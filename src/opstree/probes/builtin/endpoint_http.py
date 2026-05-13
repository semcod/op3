"""Probe dla warstwy endpoint.http — HTTP endpoint health checks."""

from __future__ import annotations
from datetime import datetime, timezone
from opstree.probes.base import ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class EndpointHttpProbe:
    """Skanuje HTTP endpoints."""

    layer_id = "endpoint.http"
    probe_name = "endpoint_http"

    def __init__(self, endpoints: list[dict] = None):
        """
        Args:
            endpoints: List of endpoint dicts with 'url' and optional 'method'
        """
        self.endpoints = endpoints or []

    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        result = ctx.execute("which curl")
        if hasattr(result, "ok"):
            return result.ok
        _, _, rc = result
        return rc == 0

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        results = []

        for endpoint in self.endpoints:
            url = endpoint.get("url", "")
            method = endpoint.get("method", "GET")

            result = self._check_endpoint(ctx, url, method)
            results.append(result)

        data = {
            "endpoints": results,
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

    def _check_endpoint(self, ctx: ProbeContext, url: str, method: str) -> dict:
        """Sprawdź pojedynczy endpoint."""

        def _exec(cmd: str) -> tuple[str, int]:
            result = ctx.execute(cmd)
            if hasattr(result, "ok"):
                return result.stdout, 0 if result.ok else 1
            return result[0], result[2]

        # Use curl to check endpoint
        stdout, rc = _exec(
            f"curl -s -o /dev/null -w '%{{http_code}}' -X {method} {url} 2>/dev/null"
        )

        try:
            status_code = int(stdout.strip()) if rc == 0 else None
        except ValueError:
            status_code = None

        # Measure response time
        stdout_time, rc_time = _exec(
            f"curl -s -o /dev/null -w '%{{time_total}}' -X {method} {url} 2>/dev/null"
        )
        try:
            response_time_ms = (
                int(float(stdout_time.strip()) * 1000) if rc_time == 0 else None
            )
        except (ValueError, AttributeError):
            response_time_ms = None

        healthy = status_code is not None and 200 <= status_code < 300

        return {
            "url": url,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "healthy": healthy,
        }

    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w endpointach."""
        anomalies = []
        endpoints = data.data.get("endpoints", [])

        for ep in endpoints:
            if not ep.get("healthy", False):
                anomalies.append(
                    {
                        "severity": "error",
                        "layer": self.layer_id,
                        "message": f"Endpoint {ep.get('url')} is unhealthy (status: {ep.get('status_code')})",
                        "evidence": {"endpoint": ep},
                    }
                )
            elif ep.get("response_time_ms", 0) > 5000:  # > 5 seconds
                anomalies.append(
                    {
                        "severity": "warning",
                        "layer": self.layer_id,
                        "message": f"Endpoint {ep.get('url')} is slow ({ep.get('response_time_ms')}ms)",
                        "evidence": {"endpoint": ep},
                    }
                )

        return anomalies
