"""Probe dla runtime kontenerów — docker, podman."""

from __future__ import annotations
from datetime import datetime, timezone
from opstree.probes.base import ProbeContext, ProbeResult
from opstree.snapshot.model import LayerData


class RuntimeContainerProbe:
    """Skanuje runtime kontenerów (docker/podman)."""

    layer_id = "runtime.container"
    probe_name = "runtime_container"

    def __init__(self, runtime: str = "auto"):
        """
        Args:
            runtime: "docker", "podman", or "auto" (detect automatically)
        """
        self.runtime = runtime

    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""

        # Check if docker or podman is available
        def _check(cmd: str) -> bool:
            result = ctx.execute(cmd)
            if hasattr(result, "ok"):
                return result.ok
            _, _, rc = result
            return rc == 0

        if self.runtime == "auto":
            return _check("which docker") or _check("which podman")
        elif self.runtime == "docker":
            return _check("which docker")
        elif self.runtime == "podman":
            return _check("which podman")
        return False

    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        runtime_name, runtime_version = self._detect_runtime(ctx)
        containers = self._list_containers(ctx, runtime_name)

        data = {
            "runtime": runtime_name,
            "version": runtime_version,
            "containers": containers,
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

    def _detect_runtime(self, ctx: ProbeContext) -> tuple[str, str]:
        """Wykryj runtime i wersję."""

        def _exec(cmd: str) -> tuple[str, int]:
            result = ctx.execute(cmd)
            if hasattr(result, "ok"):
                return result.stdout, 0 if result.ok else 1
            return result[0], result[2]

        if self.runtime == "auto":
            # Try podman first (preferred for rootless)
            stdout, rc = _exec("podman --version 2>/dev/null")
            if rc == 0:
                version = stdout.strip().split()[-1]
                return "podman", version

            # Fallback to docker
            stdout, rc = _exec("docker --version 2>/dev/null")
            if rc == 0:
                version = stdout.strip().split()[-1].strip(",")
                return "docker", version

            return "unknown", "unknown"
        else:
            stdout, rc = _exec(f"{self.runtime} --version 2>/dev/null")
            if rc == 0:
                version = stdout.strip().split()[-1].strip(",")
                return self.runtime, version
            return self.runtime, "unknown"

    def _list_containers(self, ctx: ProbeContext, runtime: str) -> list[dict]:
        """Lista kontenerów."""
        containers = []

        def _exec(cmd: str) -> tuple[str, int]:
            result = ctx.execute(cmd)
            if hasattr(result, "ok"):
                return result.stdout, 0 if result.ok else 1
            return result[0], result[2]

        # Try podman ps --format json first
        if runtime == "podman" or runtime == "auto":
            stdout, rc = _exec("podman ps -a --format json 2>/dev/null")
            if rc == 0:
                import json

                try:
                    container_list = json.loads(stdout)
                    for c in container_list:
                        containers.append(
                            {
                                "id": c.get("Id", "")[:12],
                                "name": c.get("Names", [""])[0]
                                if c.get("Names")
                                else "",
                                "image": c.get("Image", ""),
                                "state": c.get("State", ""),
                                "status": c.get("Status", ""),
                                "restart_policy": c.get("Labels", {}).get(
                                    "io.podman.annotations.restartpolicy", ""
                                ),
                            }
                        )
                    return containers
                except json.JSONDecodeError:
                    pass

        # Fallback to docker ps --format json
        if runtime == "docker" or runtime == "auto":
            stdout, rc = _exec("docker ps -a --format json 2>/dev/null")
            if rc == 0:
                import json

                try:
                    container_list = json.loads(stdout)
                    for c in container_list:
                        containers.append(
                            {
                                "id": c.get("ID", "")[:12],
                                "name": c.get("Names", ""),
                                "image": c.get("Image", ""),
                                "state": c.get("State", ""),
                                "status": c.get("Status", ""),
                                "restart_policy": c.get("Labels", {}).get(
                                    "com.docker.compose.restart", ""
                                ),
                            }
                        )
                    return containers
                except json.JSONDecodeError:
                    pass

        # Fallback to plain text parsing
        cmd = (
            f"{runtime} ps -a"
            if runtime != "unknown"
            else "docker ps -a 2>/dev/null || podman ps -a 2>/dev/null"
        )
        stdout, rc = _exec(cmd)
        if rc == 0:
            lines = stdout.strip().splitlines()
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        containers.append(
                            {
                                "id": parts[0][:12],
                                "name": parts[-1],
                                "image": parts[1],
                                "state": parts[4] if len(parts) > 4 else "",
                                "status": "",
                                "restart_policy": "",
                            }
                        )

        return containers

    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w kontenerach."""
        anomalies = []
        containers = data.data.get("containers", [])

        # Check for stopped containers that should be running
        for container in containers:
            if container.get("state") == "exited" and container.get(
                "restart_policy"
            ) in ["always", "unless-stopped"]:
                anomalies.append(
                    {
                        "severity": "warning",
                        "layer": self.layer_id,
                        "message": f"Container {container.get('name')} is stopped but has restart policy {container.get('restart_policy')}",
                        "evidence": {"container": container},
                    }
                )

        return anomalies
