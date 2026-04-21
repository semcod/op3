"""LESS format adapter — read/write doql-compatible .doql.less files."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from opstree.snapshot.model import Snapshot, PartialSnapshot, LayerData
from datetime import datetime, timezone


class LessAdapter:
    """Parsuj i emituj .doql.less."""
    format_name = "less"
    
    def parse(self, text: str) -> PartialSnapshot:
        """Parsuj LESS → PartialSnapshot."""
        layers = {}
        
        # Parse app metadata
        app_match = re.search(r'app\s*\{\s*name:\s*([^;]+);\s*version:\s*([^;]+);\s*\}', text)
        if app_match:
            app_name = app_match.group(1).strip()
            app_version = app_match.group(2).strip()
            layers["business.health"] = LayerData(
                layer_id="business.health",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "app_name": app_name,
                    "app_version": app_version,
                    "overall_health": "unknown",
                    "alerts": [],
                },
            )
        
        # Parse interface
        interface_matches = re.finditer(
            r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}',
            text,
            re.MULTILINE | re.DOTALL
        )
        for match in interface_matches:
            iface_type = match.group(1).strip()
            body = match.group(2)
            layers["physical.display"] = LayerData(
                layer_id="physical.display",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "interface_type": iface_type,
                    "config": self._parse_block(body),
                },
            )
        
        # Parse services
        service_matches = re.finditer(
            r'service\[name="([^"]+)"\]\s*\{([^}]+)\}',
            text,
            re.MULTILINE | re.DOTALL
        )
        services = []
        for match in service_matches:
            service_name = match.group(1).strip()
            body = match.group(2)
            services.append({
                "name": service_name,
                **self._parse_block(body),
            })
        
        if services:
            layers["service.containers"] = LayerData(
                layer_id="service.containers",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={"systemd_services": services},
            )
        
        # Parse environment
        env_matches = re.finditer(
            r'environment\[name="([^"]+)"\]\s*\{([^}]+)\}',
            text,
            re.MULTILINE | re.DOTALL
        )
        for match in env_matches:
            env_name = match.group(1).strip()
            body = match.group(2)
            layers["runtime.container"] = LayerData(
                layer_id="runtime.container",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "environment_name": env_name,
                    **self._parse_block(body),
                },
            )
        
        # Parse deploy
        deploy_match = re.search(r'deploy\s*\{([^}]+)\}', text, re.MULTILINE | re.DOTALL)
        if deploy_match:
            body = deploy_match.group(1)
            deploy_config = self._parse_block(body)
            layers["endpoint.http"] = LayerData(
                layer_id="endpoint.http",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "endpoints": [{
                        "url": f"http://{deploy_config.get('domain', 'localhost')}",
                        "target": deploy_config.get("target", "unknown"),
                    }],
                },
            )
        
        return PartialSnapshot(
            layers=layers,
            source_format="less",
            source_path=None,
        )
    
    def render(self, snapshot: Snapshot | PartialSnapshot, scope: List[str] | None = None) -> str:
        """Renderuj Snapshot → LESS."""
        scope = scope or ["service", "runtime"]
        lines = []
        
        # Render app metadata
        business_layer = snapshot.layers.get("business.health")
        if business_layer:
            app_name = business_layer.data.get("app_name", "unknown")
            app_version = business_layer.data.get("app_version", "0.0.0")
            lines.append(f"app {{")
            lines.append(f"  name: {app_name};")
            lines.append(f"  version: {app_version};")
            lines.append(f"}}")
            lines.append("")
        
        # Render physical display
        display_layer = snapshot.layers.get("physical.display")
        if display_layer and "physical" in scope:
            lines.append(f"interface[type=\"display\"] {{")
            for key, value in display_layer.data.items():
                if key != "interface_type":
                    lines.append(f"  {key}: {value};")
            lines.append(f"}}")
            lines.append("")
        
        # Render services
        service_layer = snapshot.layers.get("service.containers")
        if service_layer and "service" in scope:
            services = service_layer.data.get("systemd_services", [])
            for svc in services:
                name = svc.get("name", "unknown")
                lines.append(f"service[name=\"{name}\"] {{")
                for key, value in svc.items():
                    if key != "name":
                        lines.append(f"  {key}: {value};")
                lines.append(f"}}")
                lines.append("")
        
        # Render runtime
        runtime_layer = snapshot.layers.get("runtime.container")
        if runtime_layer and "runtime" in scope:
            env_name = runtime_layer.data.get("environment_name", "production")
            lines.append(f"environment[name=\"{env_name}\"] {{")
            for key, value in runtime_layer.data.items():
                if key != "environment_name":
                    lines.append(f"  {key}: {value};")
            lines.append(f"}}")
            lines.append("")
        
        # Render deploy
        endpoint_layer = snapshot.layers.get("endpoint.http")
        if endpoint_layer and "endpoint" in scope:
            endpoints = endpoint_layer.data.get("endpoints", [])
            if endpoints:
                lines.append(f"deploy {{")
                for ep in endpoints:
                    if "target" in ep:
                        lines.append(f"  target: {ep['target']};")
                    if "url" in ep:
                        domain = ep["url"].replace("http://", "").split("/")[0]
                        lines.append(f"  domain: {domain};")
                lines.append(f"}}")
        
        return "\n".join(lines)
    
    def _parse_block(self, body: str) -> Dict[str, str]:
        """Parse a LESS block into key-value pairs."""
        result = {}
        for line in body.split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("//"):
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().rstrip(";").strip()
        return result
