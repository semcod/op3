"""Unit tests for LESS format adapter."""
from datetime import datetime, timezone
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
    adapter = LessAdapter()
    
    snapshot = Snapshot(
        target="test@localhost",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.1.7",
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


# ── Sprint 3: inline comments, multi-line values, escape sequences ───────


def test_less_adapter_inline_comments_stripped():
    """Inline ``// comment`` suffixes must be removed from values."""
    adapter = LessAdapter()
    less_text = """
app {
  name: kiosk; // app identity
  version: 0.1.0;
}
"""
    result = adapter.parse(less_text)
    assert result.layers["business.health"].data["app_version"] == "0.1.0"


def test_less_adapter_multiline_value():
    """Values that span multiple lines (no ``;`` on first line) are concatenated."""
    adapter = LessAdapter()
    less_text = """
service[name="deploy"] {
  script: echo start
    echo middle
    echo end;
}
"""
    result = adapter.parse(less_text)
    svc = result.layers["service.containers"].data["systemd_services"][0]
    assert svc["script"] == "echo start\n    echo middle\n    echo end"


def test_less_adapter_escaped_semicolon_does_not_terminate():
    """A ``\\;`` inside a value must not end the multi-line continuation."""
    adapter = LessAdapter()
    less_text = """
service[name="x"] {
  cmd: if true; then
    echo ok;
}
"""
    result = adapter.parse(less_text)
    svc = result.layers["service.containers"].data["systemd_services"][0]
    assert svc["cmd"] == 'if true; then\n    echo ok'


def test_less_adapter_escape_newline():
    """``\\n`` in a single-line value is expanded to a literal newline."""
    adapter = LessAdapter()
    less_text = """
app {
  name: line1\\nline2;
  version: 1.0.0;
}
"""
    result = adapter.parse(less_text)
    assert result.layers["business.health"].data["app_name"] == "line1\nline2"


def test_less_adapter_escape_backslash():
    """``\\\\`` produces a single literal backslash."""
    adapter = LessAdapter()
    less_text = r"""
app {
  name: path\\\\to\\file;
  version: 1.0.0;
}
"""
    result = adapter.parse(less_text)
    assert result.layers["business.health"].data["app_name"] == r"path\\to\file"


def test_less_adapter_render_escapes_semicolon():
    """A ``;`` inside a value must be escaped on render so it is not mis-read."""
    adapter = LessAdapter()
    snapshot = Snapshot(
        target="t",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.2.0",
        layers={
            "business.health": LayerData(
                layer_id="business.health",
                probed_at=datetime.now(timezone.utc),
                probed_by="test",
                data={"app_name": "a;b", "app_version": "1.0.0", "overall_health": "ok", "alerts": []},
            ),
        },
    )
    rendered = adapter.render(snapshot)
    assert "name: a\\;b;" in rendered
    reparsed = adapter.parse(rendered)
    assert reparsed.layers["business.health"].data["app_name"] == "a;b"


def test_less_adapter_roundtrip_multiline():
    """Parse → render → parse must preserve a multi-line value."""
    adapter = LessAdapter()
    snapshot = Snapshot(
        target="t",
        scanned_at=datetime.now(timezone.utc),
        scanner_version="0.2.0",
        layers={
            "service.containers": LayerData(
                layer_id="service.containers",
                probed_at=datetime.now(timezone.utc),
                probed_by="test",
                data={
                    "systemd_services": [
                        {"name": "x", "cmd": "echo a\necho b\necho c"},
                    ]
                },
            ),
        },
    )
    rendered = adapter.render(snapshot)
    reparsed = adapter.parse(rendered)
    svc = reparsed.layers["service.containers"].data["systemd_services"][0]
    assert svc["cmd"] == "echo a\necho b\necho c"
