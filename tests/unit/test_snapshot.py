"""Unit tests for snapshot model and diff."""
import pytest
from datetime import datetime, timezone
from opstree.snapshot.model import Snapshot, LayerData, PartialSnapshot
from opstree.snapshot.diff import snapshot_diff, Change


def test_layer_data_creation():
    """Test LayerData creation."""
    data = LayerData(
        layer_id="test.layer",
        probed_at=datetime.now(timezone.utc),
        probed_by="test_probe",
        data={"key": "value"},
    )
    assert data.layer_id == "test.layer"
    assert data.data == {"key": "value"}


def test_snapshot_creation():
    """Test Snapshot creation."""
    snapshot = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value1"},
            )
        },
    )
    assert snapshot.target == "test@localhost"
    assert len(snapshot.layers) == 1


def test_snapshot_layer_accessor():
    """Test snapshot.layer() accessor."""
    layer_data = LayerData(
        layer_id="layer1",
        probed_at=datetime.now(timezone.utc),
        probed_by="probe1",
        data={"key": "value1"},
    )
    snapshot = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={"layer1": layer_data},
    )
    assert snapshot.layer("layer1") == layer_data
    assert snapshot.layer("nonexistent") is None


def test_snapshot_yaml_roundtrip():
    """Test YAML serialization and deserialization."""
    import yaml
    from pathlib import Path
    import tempfile
    
    snapshot = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value1"},
            )
        },
    )
    
    yaml_str = snapshot.to_yaml()
    assert "test@localhost" in yaml_str
    assert "layer1" in yaml_str
    
    # Write and read back
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_str)
        temp_path = f.name
    
    try:
        loaded = Snapshot.load(temp_path)
        assert loaded.target == snapshot.target
        assert len(loaded.layers) == len(snapshot.layers)
    finally:
        Path(temp_path).unlink()


def test_snapshot_diff_added_layer():
    """Test diff detecting added layer."""
    snapshot_a = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={},
    )
    
    snapshot_b = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value1"},
            )
        },
    )
    
    changes = snapshot_diff(snapshot_a, snapshot_b)
    assert len(changes) == 1
    assert changes[0].type == "added"
    assert changes[0].layer_id == "layer1"


def test_snapshot_diff_removed_layer():
    """Test diff detecting removed layer."""
    snapshot_a = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value1"},
            )
        },
    )
    
    snapshot_b = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={},
    )
    
    changes = snapshot_diff(snapshot_a, snapshot_b)
    assert len(changes) == 1
    assert changes[0].type == "removed"
    assert changes[0].layer_id == "layer1"


def test_snapshot_diff_modified_data():
    """Test diff detecting modified data."""
    snapshot_a = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value1"},
            )
        },
    )
    
    snapshot_b = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
        layers={
            "layer1": LayerData(
                layer_id="layer1",
                probed_at=datetime.now(timezone.utc),
                probed_by="probe1",
                data={"key": "value2"},
            )
        },
    )
    
    changes = snapshot_diff(snapshot_a, snapshot_b)
    assert len(changes) == 1
    assert changes[0].type == "modified"
    assert changes[0].old_value == "value1"
    assert changes[0].new_value == "value2"
