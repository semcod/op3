"""Uniform adapter over heterogeneous ``ProbeContext.execute`` return shapes."""

from __future__ import annotations

from dataclasses import dataclass

from opstree.probes.base import ProbeContext


@dataclass(frozen=True)
class ProbeExec:
    ok: bool
    stdout: str

    @classmethod
    def run(cls, ctx: ProbeContext, cmd: str) -> "ProbeExec":
        result = ctx.execute(cmd)
        if hasattr(result, "ok"):
            return cls(ok=bool(result.ok), stdout=getattr(result, "stdout", "") or "")
        if isinstance(result, str):
            return cls(ok=True, stdout=result)
        try:
            stdout, _stderr, rc = result
        except Exception:
            return cls(ok=False, stdout="")
        return cls(ok=(rc == 0), stdout=stdout or "")

    def text(self, default: str = "") -> str:
        return self.stdout.strip() if self.ok else default

    def lines(self) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.strip()]

    def int_(self, default: int = 0) -> int:
        if not self.ok:
            return default
        try:
            return int(self.stdout.strip())
        except (TypeError, ValueError):
            return default
