"""Generic ``Rule`` / ``Diagnostic`` / ``RuleEngine`` primitives.

Design goals
------------

* **Generic.** A ``Rule`` is parametrised by the subject type ``T``.  The
  engine makes no assumptions about what the subject is — a Snapshot,
  a dict, a pydantic model, anything.
* **Declarative.** A rule is a single record; adding a new check never
  requires editing the engine or any if/elif chain.
* **Composable.** ``Rule.message`` and ``Rule.fix`` accept either a
  static string or a callable ``T -> str``.  Both ``predicate`` and
  ``dynamic`` fan-out rules are supported — ``Rule.dynamic`` yields
  zero-or-more diagnostics, which is what redeploy needed for
  per-backlight / per-i2c-chip checks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Literal,
    Optional,
    TypeVar,
)


Severity = Literal["info", "warning", "error", "critical"]

T = TypeVar("T")


@dataclass(frozen=True)
class Diagnostic:
    """A single finding emitted by a rule.

    Kept minimal and serialisable so downstream projects can wrap it in
    their own model (e.g. ``redeploy.models.HardwareDiagnostic``).
    """

    component: str
    severity: Severity
    message: str
    fix: Optional[str] = None
    rule_name: Optional[str] = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "severity": self.severity,
            "message": self.message,
            "fix": self.fix,
            "rule_name": self.rule_name,
            "evidence": dict(self.evidence),
        }


@dataclass
class Rule(Generic[T]):
    """Declarative diagnostic rule over subject ``T``.

    Exactly one of ``predicate`` (single-shot) or ``dynamic`` (fan-out)
    must be supplied.
    """

    name: str
    component: str
    severity: Severity = "warning"

    # Single-shot form: predicate + (message, fix) -> 0 or 1 diagnostic
    predicate: Optional[Callable[[T], bool]] = None
    message: Callable[[T], str] | str | None = None
    fix: Callable[[T], str] | str | None = None
    evidence: Callable[[T], dict[str, Any]] | None = None

    # Fan-out form: returns iterable of Diagnostic (per-device rules etc.)
    dynamic: Optional[Callable[[T], Iterable[Diagnostic]]] = None

    def __post_init__(self) -> None:
        if (self.predicate is None) == (self.dynamic is None):
            raise ValueError(
                f"Rule {self.name!r} must define exactly one of "
                f"`predicate` or `dynamic`."
            )
        if self.predicate is not None and self.message is None:
            raise ValueError(
                f"Rule {self.name!r} uses `predicate` — `message` is required."
            )

    def evaluate(self, subject: T) -> list[Diagnostic]:
        """Return zero or more diagnostics produced by this rule."""
        if self.dynamic is not None:
            return list(self.dynamic(subject))

        assert self.predicate is not None  # narrowed by __post_init__
        if not self.predicate(subject):
            return []

        msg = self.message(subject) if callable(self.message) else self.message
        fix = self.fix(subject) if callable(self.fix) else self.fix
        ev = self.evidence(subject) if self.evidence else {}
        return [
            Diagnostic(
                component=self.component,
                severity=self.severity,
                message=str(msg),
                fix=fix,
                rule_name=self.name,
                evidence=ev,
            )
        ]


class RuleEngine(Generic[T]):
    """Runs a list of :class:`Rule` objects against a subject.

    Stateless and reusable; keep one per rule-set and call
    :meth:`evaluate` with whatever subjects you want to diagnose.
    """

    def __init__(self, rules: Iterable[Rule[T]]) -> None:
        self._rules: list[Rule[T]] = list(rules)

    @property
    def rules(self) -> list[Rule[T]]:
        return list(self._rules)

    def evaluate(self, subject: T) -> list[Diagnostic]:
        findings: list[Diagnostic] = []
        for rule in self._rules:
            findings.extend(rule.evaluate(subject))
        return findings

    def any_error(self, subject: T, *, exclude: Iterable[str] = ()) -> bool:
        """True iff any rule (not in *exclude*) fires at error+ severity."""
        skip = set(exclude)
        for rule in self._rules:
            if rule.name in skip:
                continue
            if rule.severity not in ("error", "critical"):
                continue
            for d in rule.evaluate(subject):
                if d.severity in ("error", "critical"):
                    return True
        return False
