"""Unit tests for layer tree and builtin layers."""
import pytest
from opstree.layers.tree import LayerTree, LayerDefinition, LayerType
from opstree.layers.builtin import (
    PhysicalLayer, OsLayer, RuntimeLayer,
    ServiceLayer, EndpointLayer, BusinessLayer,
)


def test_layer_tree_registration():
    """Test that layers can be registered in LayerTree."""
    tree = LayerTree()
    
    layer = LayerDefinition(
        id="test.layer",
        type="physical",
        depends_on=[],
    )
    
    tree.register(layer)
    assert tree.get("test.layer") == layer


def test_layer_tree_duplicate_registration():
    """Test that duplicate layer registration raises error."""
    tree = LayerTree()
    
    layer = LayerDefinition(
        id="test.layer",
        type="physical",
        depends_on=[],
    )
    
    tree.register(layer)
    
    with pytest.raises(ValueError, match="Layer already registered"):
        tree.register(layer)


def test_layer_tree_topological_order():
    """Test topological ordering of layers."""
    tree = LayerTree()
    
    tree.register(LayerDefinition(id="a", type="physical", depends_on=[]))
    tree.register(LayerDefinition(id="b", type="os", depends_on=["a"]))
    tree.register(LayerDefinition(id="c", type="runtime", depends_on=["b"]))
    
    order = tree.topological_order()
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_layer_tree_cycle_detection():
    """Test that cycles in dependencies are detected."""
    tree = LayerTree()
    
    tree.register(LayerDefinition(id="a", type="physical", depends_on=["b"]))
    tree.register(LayerDefinition(id="b", type="os", depends_on=["a"]))
    
    with pytest.raises(ValueError, match="Cycle detected"):
        tree.topological_order()


def test_builtin_layers_exist():
    """Test that all builtin layer definitions exist."""
    assert hasattr(PhysicalLayer, "display")
    assert hasattr(PhysicalLayer, "network")
    assert hasattr(PhysicalLayer, "compute")
    
    assert hasattr(OsLayer, "kernel")
    assert hasattr(OsLayer, "config")
    
    assert hasattr(RuntimeLayer, "container")
    assert hasattr(RuntimeLayer, "compositor")
    
    assert hasattr(ServiceLayer, "containers")
    assert hasattr(ServiceLayer, "systemd")
    
    assert hasattr(EndpointLayer, "http")
    assert hasattr(EndpointLayer, "tcp")
    
    assert hasattr(BusinessLayer, "health")


def test_builtin_layer_dependencies():
    """Test that builtin layers have correct dependencies."""
    assert PhysicalLayer.display.depends_on == []
    assert OsLayer.kernel.depends_on == ["physical.compute"]
    assert RuntimeLayer.container.depends_on == ["os.kernel"]
    assert RuntimeLayer.compositor.depends_on == ["physical.display", "os.kernel"]
