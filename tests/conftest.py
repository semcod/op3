"""Pytest configuration for op3 tests."""

import pytest
from opstree.layers.tree import LayerTree
from opstree.layers.builtin import (
    PhysicalLayer,
    OsLayer,
    RuntimeLayer,
    ServiceLayer,
    EndpointLayer,
    BusinessLayer,
)


@pytest.fixture
def layer_tree() -> LayerTree:
    """Fixture providing a LayerTree with all builtin layers registered."""
    tree = LayerTree()

    # Register all builtin layers
    tree.register(PhysicalLayer.display)
    tree.register(PhysicalLayer.network)
    tree.register(PhysicalLayer.compute)
    tree.register(OsLayer.kernel)
    tree.register(OsLayer.config)
    tree.register(RuntimeLayer.container)
    tree.register(RuntimeLayer.compositor)
    tree.register(ServiceLayer.containers)
    tree.register(ServiceLayer.systemd)
    tree.register(EndpointLayer.http)
    tree.register(EndpointLayer.tcp)
    tree.register(BusinessLayer.health)

    return tree
