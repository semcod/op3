"""Generic diagnostic rule engine.

Projects such as ``redeploy`` and ``doql`` frequently need to take a piece
of observed state and turn it into a human-facing diagnosis plus an
actionable fix.  Historically each project rolled its own mini-engine —
this module centralises it.

Usage::

    from opstree.diagnostics import Rule, RuleEngine

    rules = [
        Rule(
            name="no_dsi_overlay",
            component="overlay",
            severity="error",
            predicate=lambda d: "dsi" not in (d.get("overlays") or []),
            message="No DSI dtoverlay found in config.txt",
            fix="Add dtoverlay=vc4-kms-dsi-... and reboot",
        ),
    ]

    diagnostics = RuleEngine(rules).evaluate(state_dict)

The engine is generic over the subject type — any ``T`` works, because
predicates / messages / fixes are plain callables.
"""

from opstree.diagnostics.rules import (
    Diagnostic,
    Rule,
    RuleEngine,
    Severity,
)

__all__ = [
    "Diagnostic",
    "Rule",
    "RuleEngine",
    "Severity",
]
