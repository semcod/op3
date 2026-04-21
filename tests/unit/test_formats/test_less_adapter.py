"""Unit tests for LESS format adapter."""
import pytest
from pathlib import Path
from opstree.formats.less import LessAdapter
from opstree.snapshot.model import Snapshot, PartialSnapshot, LayerData


FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


def test_less_adapter_parse():
    """Test parsing LESS to PartialSnapshot."""
    adapter = LessAdapter()
    less_text = """
app {
  name: kiosk;
  version: 0.1.123;
}

service[name="kiosk-browser"] {
  image: localhost/kiosk-browser:latest;
  restart: always;
}
"""
    
    result = adapter.parse(less_text)
    assert isinstance(result, PartialSnapshot)
    assert result.source_format == "less"
    assert "business.health" in result.layers
    assert result.layers["business.health"].data["app_name"] == "kiosk"
    assert result.layers["business.health"].data["app_version"] == "0.1.123"


def test_less_adapter_render():
    """Test rendering Snapshot to LESS."""
    from datetime import datetime, timezone
    adapter = LessAdapter()
    
    snapshot = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.5",
        layers={
            "business.health": LayerData(
                layer_id="business.health",
                probed_at=datetime.now(timezone.utc),
                probed_by="test",
                data={
                    "app_name": "test-app",
                    "app_version": "1.0.0",
                    "overall_health": "healthy",
                    "alerts": [],
                }
            ),
        },
    )
    
    result = adapter.render(snapshot)
    assert "app {" in result
    assert "name: test-app;" in result
    assert "version: 1.0.0;" in result


def test_less_adapter_roundtrip():
    """Test round-trip: parse → render → parse."""
    adapter = LessAdapter()
    
    # Load original from fixture
    original_less = (FIXTURES / "sample.doql.less").read_text()
    
    # Parse
    parsed = adapter.parse(original_less)
    
    # Render
    rendered = adapter.render(parsed)
    
    # Parse again
    reparsed = adapter.parse(rendered)
    
    # Check that business layer is preserved
    assert "business.health" in parsed.layers
    assert "business.health" in reparsed.layers
    
    # Check app name is preserved
    assert parsed.layers["business.health"].data["app_name"] == \
           reparsed.layers["business.health"].data["app_name"]
