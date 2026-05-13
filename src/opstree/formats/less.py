"""LESS format adapter — read/write doql-compatible .doql.less files."""

from __future__ import annotations
import re
from typing import Any, Dict, List
from opstree.snapshot.model import Snapshot, PartialSnapshot, LayerData
from datetime import datetime, timezone


class LessAdapter:
    """Parsuj i emituj .doql.less."""

    format_name = "less"

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _strip_inline_comment(line: str) -> str:
        """Remove ``// ...`` suffix from *line* (not inside string literals)."""
        # Simple scan: find "//" that is not preceded by an odd number of backslashes.
        # This is intentionally basic — we only need to strip trailing comments,
        # not full JavaScript/LESS expression parsing.
        idx = 0
        while True:
            pos = line.find("//", idx)
            if pos == -1:
                return line
            # Check whether the slashes are escaped: \// or \\// etc.
            back_count = 0
            p = pos - 1
            while p >= 0 and line[p] == "\\":
                back_count += 1
                p -= 1
            if back_count % 2 == 1:
                idx = pos + 2
                continue
            return line[:pos]

    @staticmethod
    def _is_terminated(text: str) -> bool:
        """Return ``True`` iff *text* ends with an unescaped ``;``."""
        if not text.endswith(";"):
            return False
        back_count = 0
        p = len(text) - 2
        while p >= 0 and text[p] == "\\":
            back_count += 1
            p -= 1
        return back_count % 2 == 0

    @staticmethod
    def _escape_value(value: str) -> str:
        r"""Escape ``\``, ``;``, and ``"`` for LESS serialization.

        Literal newlines are left untouched — :meth:`_render_key_value`
        handles them by splitting into continuation lines.
        """
        return value.replace("\\", "\\\\").replace(";", "\\;").replace('"', '\\"')

    @staticmethod
    def _unescape_value(value: str) -> str:
        r"""Reverse of :meth:`_escape_value` plus ``\n`` → newline."""
        # Order matters: unescape backslashes last.
        return (
            value.replace("\\;", ";")
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\\\", "\\")
        )

    @staticmethod
    def _render_key_value(
        key: str, value: Any, lines: list[str], indent: str = "  "
    ) -> None:
        """Append ``key: value;`` (or multi-line continuation) to *lines*."""
        str_val = str(value)
        if "\n" in str_val:
            escaped = LessAdapter._escape_value(str_val)
            parts = escaped.split("\n")
            lines.append(f"{indent}{key}: {parts[0]}")
            for part in parts[1:-1]:
                lines.append(part)
            lines.append(f"{parts[-1]};")
        else:
            escaped = LessAdapter._escape_value(str_val)
            lines.append(f"{indent}{key}: {escaped};")

    # ── parse / render ──────────────────────────────────────────────────────

    def parse(self, text: str) -> PartialSnapshot:
        """Parsuj LESS → PartialSnapshot."""
        layers = {}

        # Parse app metadata — extract block body so _parse_block handles
        # inline comments, multi-line values, and escapes uniformly.
        app_match = re.search(r"app\s*\{([^}]*)\}", text, re.MULTILINE | re.DOTALL)
        if app_match:
            app_data = self._parse_block(app_match.group(1))
            layers["business.health"] = LayerData(
                layer_id="business.health",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "app_name": app_data.get("name", "unknown"),
                    "app_version": app_data.get("version", "0.0.0"),
                    "overall_health": "unknown",
                    "alerts": [],
                },
            )

        # Parse interface
        interface_matches = re.finditer(
            r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}', text, re.MULTILINE | re.DOTALL
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
            r'service\[name="([^"]+)"\]\s*\{([^}]+)\}', text, re.MULTILINE | re.DOTALL
        )
        services = []
        for match in service_matches:
            service_name = match.group(1).strip()
            body = match.group(2)
            services.append(
                {
                    "name": service_name,
                    **self._parse_block(body),
                }
            )

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
            re.MULTILINE | re.DOTALL,
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
        deploy_match = re.search(
            r"deploy\s*\{([^}]+)\}", text, re.MULTILINE | re.DOTALL
        )
        if deploy_match:
            body = deploy_match.group(1)
            deploy_config = self._parse_block(body)
            layers["endpoint.http"] = LayerData(
                layer_id="endpoint.http",
                probed_at=datetime.now(timezone.utc),
                probed_by="less_parser",
                data={
                    "endpoints": [
                        {
                            "url": f"http://{deploy_config.get('domain', 'localhost')}",
                            "target": deploy_config.get("target", "unknown"),
                        }
                    ],
                },
            )

        return PartialSnapshot(
            layers=layers,
            source_format="less",
            source_path=None,
        )

    def render(
        self, snapshot: Snapshot | PartialSnapshot, scope: List[str] | None = None
    ) -> str:
        """Renderuj Snapshot → LESS."""
        scope = scope or ["service", "runtime"]
        lines = []

        # Render app metadata
        business_layer = snapshot.layers.get("business.health")
        if business_layer:
            app_name = business_layer.data.get("app_name", "unknown")
            app_version = business_layer.data.get("app_version", "0.0.0")
            lines.append("app {")
            self._render_key_value("name", app_name, lines)
            self._render_key_value("version", app_version, lines)
            lines.append("}")
            lines.append("")

        # Render physical display
        display_layer = snapshot.layers.get("physical.display")
        if display_layer and "physical" in scope:
            lines.append('interface[type="display"] {')
            for key, value in display_layer.data.items():
                if key != "interface_type":
                    self._render_key_value(key, value, lines)
            lines.append("}")
            lines.append("")

        # Render services
        service_layer = snapshot.layers.get("service.containers")
        if service_layer and "service" in scope:
            services = service_layer.data.get("systemd_services", [])
            for svc in services:
                name = svc.get("name", "unknown")
                lines.append(f'service[name="{name}"] {{')
                for key, value in svc.items():
                    if key != "name":
                        self._render_key_value(key, value, lines)
                lines.append("}")
                lines.append("")

        # Render runtime
        runtime_layer = snapshot.layers.get("runtime.container")
        if runtime_layer and "runtime" in scope:
            env_name = runtime_layer.data.get("environment_name", "production")
            lines.append(f'environment[name="{env_name}"] {{')
            for key, value in runtime_layer.data.items():
                if key != "environment_name":
                    self._render_key_value(key, value, lines)
            lines.append("}")
            lines.append("")

        # Render deploy
        endpoint_layer = snapshot.layers.get("endpoint.http")
        if endpoint_layer and "endpoint" in scope:
            endpoints = endpoint_layer.data.get("endpoints", [])
            if endpoints:
                lines.append("deploy {")
                for ep in endpoints:
                    if "target" in ep:
                        self._render_key_value("target", ep["target"], lines)
                    if "url" in ep:
                        domain = ep["url"].replace("http://", "").split("/")[0]
                        self._render_key_value("domain", domain, lines)
                lines.append("}")

        return "\n".join(lines)

    def _parse_block(self, body: str) -> Dict[str, str]:
        """Parse a LESS block into key-value pairs.

        Supports:
        - Full-line and inline ``//`` comments (stripped).
        - Multi-line values: a line ending without an unescaped ``;``
          continues onto the next line(s) until the terminator appears.
        - Escapes: ``\\;``, ``\\"``, ``\\n`` → newline, ``\\\\`` → ``\\``.
        """
        result: Dict[str, str] = {}
        lines = body.split("\n")
        current_key: str | None = None
        current_parts: list[str] = []

        def _flush() -> None:
            nonlocal current_key
            if current_key is None:
                return
            raw = "\n".join(current_parts).strip()
            # Strip the unescaped terminator semicolon before unescaping.
            if self._is_terminated(raw):
                raw = raw[:-1].rstrip()
            result[current_key] = self._unescape_value(raw)
            current_key = None
            current_parts.clear()

        for raw_line in lines:
            line = self._strip_inline_comment(raw_line).rstrip()
            if not line:
                continue

            # A line containing ':' starts a new key — unless we are already
            # in a continuation and ':' is part of the value. In current
            # doql.less syntax keys never contain ':' so any ':' before the
            # first terminator belongs to a new key declaration.
            if ":" in line and current_key is None:
                _flush()
                key, value = line.split(":", 1)
                current_key = key.strip()
                current_parts = [value.strip()]
            elif current_key is not None:
                # Preserve leading whitespace — only strip trailing so that
                # indented heredocs / Makefiles inside multi-line values survive.
                current_parts.append(line.rstrip())
            else:
                # Stray line with no active key — ignore.
                pass

            if current_key is not None:
                joined = "\n".join(current_parts)
                if self._is_terminated(joined):
                    _flush()

        _flush()
        return result
