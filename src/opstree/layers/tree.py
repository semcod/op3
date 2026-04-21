"""LayerTree — hierarchia warstw zbudowana na FraqNode."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
from fraq import FraqNode, FraqSchema

LayerType = Literal[
    "physical", "os", "runtime", "service", "endpoint", "business",
    # compound layers:
    "physical.display", "physical.network", "physical.compute",
    "os.kernel", "os.config",
    "runtime.container", "runtime.compositor",
    "service.containers", "service.systemd",
    "endpoint.http", "endpoint.tcp",
]


@dataclass(frozen=True)
class LayerDefinition:
    """Definicja jednej warstwy w drzewie."""
    id: str                           # np. "physical.display"
    type: LayerType
    depends_on: list[str] = field(default_factory=list)  # inne warstwy które muszą być zeskanowane pierwsze
    schema: type | None = None        # Pydantic model dla danych tej warstwy
    
    def to_fraq_node(self) -> FraqNode:
        """Konwertuj na FraqNode dla użycia przez fraq.core."""
        # Używamy pozycji w hiperprzestrzeni jako koordynatów warstwy
        # wymiary: (depth, category, instance)
        depth = len(self.id.split("."))
        category_hash = hash(self.type) & 0xFFFF
        return FraqNode(
            position=(float(depth), float(category_hash), 0.0),
            metadata={"layer_id": self.id, "layer_type": self.type},
        )


class LayerTree:
    """Drzewo warstw — topological ordering, dependency resolution."""
    
    def __init__(self):
        self._layers: dict[str, LayerDefinition] = {}
        self._schema = FraqSchema()
    
    def register(self, layer: LayerDefinition) -> None:
        if layer.id in self._layers:
            raise ValueError(f"Layer already registered: {layer.id}")
        self._layers[layer.id] = layer
        # Dodaj do FraqSchema dla future query/export
        if layer.schema is not None:
            for field_name, field_type in layer.schema.model_fields.items():
                self._schema.add_field(f"{layer.id}.{field_name}", str(field_type.annotation))
    
    def get(self, layer_id: str) -> LayerDefinition | None:
        return self._layers.get(layer_id)
    
    def topological_order(self) -> list[str]:
        """Zwróć warstwy w kolejności do skanowania (DAG)."""
        # Standard Kahn's algorithm
        in_degree = {lid: 0 for lid in self._layers}
        for layer in self._layers.values():
            for dep in layer.depends_on:
                in_degree[layer.id] += 1
        
        queue = [lid for lid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            for layer in self._layers.values():
                if current in layer.depends_on:
                    in_degree[layer.id] -= 1
                    if in_degree[layer.id] == 0:
                        queue.append(layer.id)
        
        if len(result) != len(self._layers):
            raise ValueError("Cycle detected in layer dependencies")
        return result
    
    def to_fraq_node(self) -> FraqNode:
        """Konwertuj całe drzewo warstw na FraqNode."""
        root = FraqNode(position=(0.0, 0.0, 0.0))
        for layer_id in self.topological_order():
            layer = self._layers[layer_id]
            child = layer.to_fraq_node()
            root._children[child.position] = child
        return root
