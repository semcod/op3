"""Built-in layer definitions for common infrastructure."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from opstree.layers.tree import LayerDefinition


# Pydantic models for layer data
class PhysicalDisplayData(BaseModel):
    board_model: str
    drm_outputs: List[Dict[str, Any]]
    backlights: List[Dict[str, Any]]
    kms_enabled: bool
    kms_driver: Optional[str] = None


class OsKernelData(BaseModel):
    version: str
    arch: str
    hostname: str
    uptime_seconds: int


class OsConfigData(BaseModel):
    config_txt: str
    cmdline: str


class RuntimeContainerData(BaseModel):
    runtime: str
    version: str
    containers: List[Dict[str, Any]]


class RuntimeCompositorData(BaseModel):
    compositor: str
    version: str
    kanshi_enabled: bool
    kanshi_profiles: List[Dict[str, Any]]
    active_profile: Optional[str] = None


class ServiceContainersData(BaseModel):
    systemd_services: List[Dict[str, Any]]


class EndpointHttpData(BaseModel):
    endpoints: List[Dict[str, Any]]


class BusinessHealthData(BaseModel):
    app_name: str
    app_version: str
    overall_health: str
    alerts: List[Dict[str, Any]]


# Layer definitions
PHYSICAL_DISPLAY = LayerDefinition(
    id="physical.display",
    type="physical.display",
    depends_on=[],
    schema=PhysicalDisplayData,
)

PHYSICAL_NETWORK = LayerDefinition(
    id="physical.network",
    type="physical.network",
    depends_on=[],
    schema=None,  # TODO: define model
)

PHYSICAL_COMPUTE = LayerDefinition(
    id="physical.compute",
    type="physical.compute",
    depends_on=[],
    schema=None,  # TODO: define model
)

OS_KERNEL = LayerDefinition(
    id="os.kernel",
    type="os.kernel",
    depends_on=["physical.compute"],
    schema=OsKernelData,
)

OS_CONFIG = LayerDefinition(
    id="os.config",
    type="os.config",
    depends_on=["os.kernel"],
    schema=OsConfigData,
)

RUNTIME_CONTAINER = LayerDefinition(
    id="runtime.container",
    type="runtime.container",
    depends_on=["os.kernel"],
    schema=RuntimeContainerData,
)

RUNTIME_COMPOSITOR = LayerDefinition(
    id="runtime.compositor",
    type="runtime.compositor",
    depends_on=["physical.display", "os.kernel"],
    schema=RuntimeCompositorData,
)

SERVICE_CONTAINERS = LayerDefinition(
    id="service.containers",
    type="service.containers",
    depends_on=["runtime.container"],
    schema=ServiceContainersData,
)

SERVICE_SYSTEMD = LayerDefinition(
    id="service.systemd",
    type="service.systemd",
    depends_on=["os.kernel"],
    schema=None,  # TODO: define model
)

ENDPOINT_HTTP = LayerDefinition(
    id="endpoint.http",
    type="endpoint.http",
    depends_on=["service.containers"],
    schema=EndpointHttpData,
)

ENDPOINT_TCP = LayerDefinition(
    id="endpoint.tcp",
    type="endpoint.tcp",
    depends_on=["service.containers"],
    schema=None,  # TODO: define model
)

BUSINESS_HEALTH = LayerDefinition(
    id="business.health",
    type="business",
    depends_on=["endpoint.http"],
    schema=BusinessHealthData,
)


# Convenience classes for grouping layers
class PhysicalLayer:
    """Physical infrastructure layer."""

    display = PHYSICAL_DISPLAY
    network = PHYSICAL_NETWORK
    compute = PHYSICAL_COMPUTE


class OsLayer:
    """Operating system layer."""

    kernel = OS_KERNEL
    config = OS_CONFIG


class RuntimeLayer:
    """Runtime environment layer."""

    container = RUNTIME_CONTAINER
    compositor = RUNTIME_COMPOSITOR


class ServiceLayer:
    """Services layer."""

    containers = SERVICE_CONTAINERS
    systemd = SERVICE_SYSTEMD


class EndpointLayer:
    """Network endpoints layer."""

    http = ENDPOINT_HTTP
    tcp = ENDPOINT_TCP


class BusinessLayer:
    """Business logic layer."""

    health = BUSINESS_HEALTH
