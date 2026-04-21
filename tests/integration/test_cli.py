"""Integration tests for CLI commands."""
import pytest
from click.testing import CliRunner
from pathlib import Path
from opstree.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "op3" in result.output
    assert "scan" in result.output
    assert "drift" in result.output
    assert "convert" in result.output


def test_cli_scan_help(runner):
    """Test scan command help."""
    result = runner.invoke(cli, ["scan", "--help"])
    assert result.exit_code == 0
    assert "Scan a device" in result.output
    assert "--ssh" in result.output
    assert "--output" in result.output


def test_cli_convert_help(runner):
    """Test convert command help."""
    result = runner.invoke(cli, ["convert", "--help"])
    assert result.exit_code == 0
    assert "Convert between configuration formats" in result.output
    assert "--format" in result.output


def test_cli_convert_less_to_snapshot_yaml(runner, tmp_path):
    """Test converting LESS to snapshot.yaml."""
    input_file = Path(__file__).parent.parent / "fixtures" / "sample.doql.less"
    output_file = tmp_path / "converted.yaml"
    
    result = runner.invoke(cli, [
        "convert",
        str(input_file),
        str(output_file),
        "--format", "snapshot_yaml"
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    
    # Verify output is valid YAML
    import yaml
    data = yaml.safe_load(output_file.read_text())
    assert "target" in data
    assert "layers" in data
    assert "business.health" in data["layers"]


def test_cli_convert_less_to_migration_yaml(runner, tmp_path):
    """Test converting LESS to migration.yaml."""
    input_file = Path(__file__).parent.parent / "fixtures" / "sample.doql.less"
    output_file = tmp_path / "converted.yaml"
    
    result = runner.invoke(cli, [
        "convert",
        str(input_file),
        str(output_file),
        "--format", "migration_yaml"
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    
    # Verify output is valid YAML with migration structure
    import yaml
    data = yaml.safe_load(output_file.read_text())
    assert "source" in data or "target" in data


def test_cli_convert_less_to_less(runner, tmp_path):
    """Test converting LESS to LESS (round-trip)."""
    input_file = Path(__file__).parent.parent / "fixtures" / "sample.doql.less"
    output_file = tmp_path / "converted.less"
    
    result = runner.invoke(cli, [
        "convert",
        str(input_file),
        str(output_file),
        "--format", "less"
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    
    # Verify output contains app block
    content = output_file.read_text()
    assert "app {" in content
    assert "name: kiosk;" in content
