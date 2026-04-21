"""Snapshot — niemutowalna migawka warstw."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class LayerData(BaseModel):
    """Dane jednej warstwy."""
    model_config = {"frozen": True}
    
    layer_id: str
    probed_at: datetime
    probed_by: str                     # nazwa Probe który zebrał dane
    data: dict[str, Any]
    raw_evidence: dict[str, Any] = Field(default_factory=dict)  # dla debuggowania


class Snapshot(BaseModel):
    """Pełna migawka urządzenia/systemu."""
    model_config = {"frozen": True}
    
    target: str                        # np. "pi@192.168.188.109"
    scanned_at: datetime
    scanner_version: str
    layers: dict[str, LayerData] = Field(default_factory=dict)
    anomalies: list = Field(default_factory=list)  # list[Anomaly] ale avoiding circular import
    
    def layer(self, layer_id: str) -> LayerData | None:
        return self.layers.get(layer_id)
    
    def query(self, expr: str) -> Any:
        """JMESPath query na snapshot."""
        import jmespath
        return jmespath.search(expr, self.model_dump())
    
    def to_yaml(self) -> str:
        import yaml
        return yaml.safe_dump(self.model_dump(mode="json"), sort_keys=False)
    
    @classmethod
    def load(cls, path) -> "Snapshot":
        import yaml
        from pathlib import Path
        data = yaml.safe_load(Path(path).read_text())
        return cls.model_validate(data)


class PartialSnapshot(BaseModel):
    """Niepełna migawka — np. z parsowania LESS-a gdzie nie ma wszystkich warstw."""
    model_config = {"frozen": True}
    
    layers: dict[str, LayerData] = Field(default_factory=dict)
    source_format: str                 # "less", "migration_yaml"
    source_path: str | None = None
