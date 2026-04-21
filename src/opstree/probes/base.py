"""Probe protocol — każdy probe skanuje jedną warstwę."""
from __future__ import annotations
from typing import Protocol, runtime_checkable, Any
from dataclasses import dataclass
from opstree.snapshot.model import LayerData


@dataclass
class ProbeContext:
    """Kontekst dla probe — nie wie o SSH, click, nic konkretnego."""
    target: str
    execute: callable                  # callable(cmd: str) -> (stdout: str, stderr: str, returncode: int)
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProbeResult:
    """Wynik probe'a."""
    layer_data: LayerData
    success: bool = True
    error: str | None = None


@runtime_checkable
class Probe(Protocol):
    """Kontrakt probe'a."""
    layer_id: str
    probe_name: str
    
    def can_probe(self, ctx: ProbeContext) -> bool:
        """Czy ten probe może pobiec w tym kontekście?"""
        ...
    
    def scan(self, ctx: ProbeContext) -> ProbeResult:
        """Zeskanuj warstwę."""
        ...
    
    def anomalies(self, data: LayerData) -> list:
        """Wykryj anomalie w zeskanowanych danych."""
        ...
