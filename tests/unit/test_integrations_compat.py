"""Tests for :mod:`opstree.integrations.compat`."""

from __future__ import annotations


import pytest

from opstree.integrations import make_compat_helpers


def _make(monkeypatch, env_value=None):
    monkeypatch.delenv("TEST_USE_OP3", raising=False)
    if env_value is not None:
        monkeypatch.setenv("TEST_USE_OP3", env_value)
    return make_compat_helpers(
        env_var="TEST_USE_OP3",
        default_layers=("physical.display", "os.kernel"),
        install_hint="pip install 'test-pkg[op3]'",
    )


def test_op3_available_true():
    h = make_compat_helpers(env_var="NOPE", default_layers=(), install_hint="nope")
    # opstree is always importable from within its own tests.
    assert h.op3_available() is True


def test_op3_enabled_truthy_values(monkeypatch):
    for raw in ("1", "true", "YES", "On", "  true  "):
        h = _make(monkeypatch, raw)
        assert h.op3_enabled() is True, raw


def test_op3_enabled_falsy_values(monkeypatch):
    for raw in ("0", "false", "no", "off", ""):
        h = _make(monkeypatch, raw)
        assert h.op3_enabled() is False, repr(raw)


def test_op3_enabled_env_absent(monkeypatch):
    h = _make(monkeypatch, None)
    assert h.op3_enabled() is False


def test_should_use_op3(monkeypatch):
    h = _make(monkeypatch, "1")
    assert h.should_use_op3() is True

    h2 = _make(monkeypatch, "0")
    assert h2.should_use_op3() is False


def test_require_op3_passes_when_available():
    h = make_compat_helpers(env_var="X", default_layers=(), install_hint="x")
    # Does not raise.
    h.require_op3("test feature")


def test_make_mock_context_round_trip():
    h = make_compat_helpers(env_var="X", default_layers=(), install_hint="x")
    ctx = h.make_mock_context({"echo hi": ("hi\n", "", 0)})
    r = ctx.execute("echo hi")
    assert r.stdout == "hi\n"
    assert r.returncode == 0


def test_make_ssh_context_factory():
    h = make_compat_helpers(env_var="X", default_layers=(), install_hint="x")
    ctx = h.make_ssh_context("user@host", ssh_key="/tmp/key")
    assert ctx.target == "user@host"


def test_make_scanner_uses_defaults():
    h = make_compat_helpers(
        env_var="X",
        default_layers=("os.kernel",),
        install_hint="x",
    )
    scanner = h.make_scanner()
    # No explicit assert on scanner internals — just make sure it's callable
    # and returns an op3 LinearScanner-like object with a scan() method.
    assert hasattr(scanner, "scan")


def test_make_scanner_respects_override():
    h = make_compat_helpers(
        env_var="X",
        default_layers=("os.kernel",),
        install_hint="x",
    )
    scanner = h.make_scanner(["physical.display"])
    assert hasattr(scanner, "scan")


def test_compat_helpers_frozen():
    h = make_compat_helpers(env_var="X", default_layers=(), install_hint="x")
    with pytest.raises((AttributeError, Exception)):
        h.env_var = "Y"  # type: ignore[misc]
