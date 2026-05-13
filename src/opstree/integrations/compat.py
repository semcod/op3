"""Reusable op3 compatibility helpers for downstream projects.

Both doql and redeploy had near-identical ``op3_bridge`` modules with
the same feature-detect, env-var opt-in, ssh/mock context, and scanner
factory helpers.  :func:`make_compat_helpers` returns a single
:class:`CompatHelpers` bundle parameterised by project-specific values
(env var name, default layer set, install hint).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional, Sequence

if TYPE_CHECKING:  # pragma: no cover
    from opstree.probes.base import Probe
    from opstree.probes.context import ProbeContext, SSHContext
    from opstree.scanner.linear import LinearScanner


@dataclass(frozen=True)
class CompatHelpers:
    """Bundle of callables produced by :func:`make_compat_helpers`.

    All callables are standalone — no instance state beyond the config
    passed to the factory, so the bundle is safe to unpack at module
    import time.
    """

    env_var: str
    default_layers: tuple[str, ...]
    install_hint: str

    op3_available: Callable[[], bool]
    op3_enabled: Callable[[], bool]
    should_use_op3: Callable[[], bool]
    require_op3: Callable[[str], None]
    make_ssh_context: Callable[..., "SSHContext"]
    make_mock_context: Callable[[dict], "ProbeContext"]
    make_scanner: Callable[..., "LinearScanner"]


def make_compat_helpers(
    *,
    env_var: str,
    default_layers: Sequence[str],
    install_hint: str,
) -> CompatHelpers:
    """Build a :class:`CompatHelpers` bundle for a downstream project.

    Parameters
    ----------
    env_var:
        Environment variable name that toggles op3 usage, e.g.
        ``"DOQL_USE_OP3"`` or ``"REDEPLOY_USE_OP3"``.
    default_layers:
        Layer ids to scan when the caller of ``make_scanner`` doesn't
        supply an explicit list.
    install_hint:
        Shown in :class:`RuntimeError` raised by ``require_op3`` when
        op3 is not importable.
    """
    default_layers_t = tuple(default_layers)

    def op3_available() -> bool:
        try:
            import opstree  # noqa: F401

            return True
        except ImportError:
            return False

    def op3_enabled() -> bool:
        raw = os.environ.get(env_var, "0")
        return raw.strip().lower() in ("1", "true", "yes", "on")

    def should_use_op3() -> bool:
        return op3_enabled() and op3_available()

    def require_op3(feature: str) -> None:
        if op3_available():
            return
        raise RuntimeError(f"{feature} requires op3. Install: {install_hint}")

    def make_ssh_context(target: str, ssh_key: Optional[str] = None):
        from opstree.probes.context import SSHContext

        return SSHContext(target=target, ssh_key_path=ssh_key)

    def make_mock_context(responses: dict[str, tuple[str, str, int]]):
        from opstree.probes.context import ExecuteResult, MockContext

        normalised = {
            cmd: ExecuteResult(stdout=out, stderr=err, returncode=rc)
            for cmd, (out, err, rc) in responses.items()
        }
        return MockContext(responses=normalised)

    def make_scanner(
        layer_ids: Optional[Sequence[str]] = None,
        *,
        extra_probes: Optional[dict[str, list["Probe"]]] = None,
    ):
        from opstree.scanner.build import build_scanner as _build_scanner

        requested = list(layer_ids) if layer_ids else list(default_layers_t)
        return _build_scanner(requested, extra_probes=extra_probes)

    return CompatHelpers(
        env_var=env_var,
        default_layers=default_layers_t,
        install_hint=install_hint,
        op3_available=op3_available,
        op3_enabled=op3_enabled,
        should_use_op3=should_use_op3,
        require_op3=require_op3,
        make_ssh_context=make_ssh_context,
        make_mock_context=make_mock_context,
        make_scanner=make_scanner,
    )
