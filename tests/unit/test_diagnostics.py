"""Unit tests for the generic diagnostic rule engine."""

from __future__ import annotations

import pytest

from opstree.diagnostics import Diagnostic, Rule, RuleEngine


def test_rule_requires_exactly_one_of_predicate_or_dynamic():
    with pytest.raises(ValueError):
        Rule(name="bad", component="c")  # neither
    with pytest.raises(ValueError):
        Rule(
            name="bad",
            component="c",
            predicate=lambda s: True,
            dynamic=lambda s: [],
            message="x",
        )  # both


def test_predicate_rule_requires_message():
    with pytest.raises(ValueError):
        Rule(name="bad", component="c", predicate=lambda s: True)


def test_predicate_rule_fires_and_returns_diagnostic():
    rule = Rule(
        name="x",
        component="net",
        severity="error",
        predicate=lambda s: s["value"] > 10,
        message=lambda s: f"too big: {s['value']}",
        fix="scale down",
    )
    diags = rule.evaluate({"value": 42})
    assert len(diags) == 1
    d = diags[0]
    assert d.component == "net"
    assert d.severity == "error"
    assert "42" in d.message
    assert d.fix == "scale down"
    assert d.rule_name == "x"


def test_predicate_rule_does_not_fire_returns_empty():
    rule = Rule(
        name="x",
        component="net",
        predicate=lambda s: False,
        message="never",
    )
    assert rule.evaluate({}) == []


def test_dynamic_rule_fans_out_multiple_diagnostics():
    def _gen(subject: dict):
        for item in subject.get("items", []):
            yield Diagnostic(
                component="item",
                severity="warning",
                message=f"item {item}",
            )

    rule = Rule(name="fan", component="item", dynamic=_gen)
    diags = rule.evaluate({"items": ["a", "b", "c"]})
    assert [d.message for d in diags] == ["item a", "item b", "item c"]


def test_static_message_and_fix_strings():
    rule = Rule(
        name="static",
        component="c",
        predicate=lambda s: True,
        message="static message",
        fix="static fix",
    )
    (d,) = rule.evaluate(None)
    assert d.message == "static message"
    assert d.fix == "static fix"


def test_rule_evidence_callable():
    rule = Rule(
        name="e",
        component="c",
        predicate=lambda s: True,
        message="m",
        evidence=lambda s: {"x": s["x"]},
    )
    (d,) = rule.evaluate({"x": 7})
    assert d.evidence == {"x": 7}


def test_engine_aggregates_all_rules():
    rules = [
        Rule(
            name="a",
            component="c",
            severity="info",
            predicate=lambda s: True,
            message="a",
        ),
        Rule(
            name="b",
            component="c",
            severity="error",
            predicate=lambda s: True,
            message="b",
        ),
        Rule(
            name="c",
            component="c",
            predicate=lambda s: False,
            message="never",
        ),
    ]
    engine = RuleEngine(rules)
    diags = engine.evaluate(object())
    assert [d.rule_name for d in diags] == ["a", "b"]


def test_engine_any_error_detects_firing_error_rule():
    rules = [
        Rule(
            name="warn",
            component="c",
            severity="warning",
            predicate=lambda s: True,
            message="w",
        ),
        Rule(
            name="err",
            component="c",
            severity="error",
            predicate=lambda s: s["bad"],
            message="e",
        ),
    ]
    engine = RuleEngine(rules)
    assert engine.any_error({"bad": True})
    assert not engine.any_error({"bad": False})


def test_engine_any_error_respects_exclude():
    rules = [
        Rule(
            name="err",
            component="c",
            severity="error",
            predicate=lambda s: True,
            message="e",
        ),
    ]
    engine = RuleEngine(rules)
    assert engine.any_error(None)
    assert not engine.any_error(None, exclude=("err",))


def test_diagnostic_to_dict_is_plain():
    d = Diagnostic(
        component="c",
        severity="info",
        message="m",
        fix=None,
        rule_name="r",
        evidence={"k": 1},
    )
    assert d.to_dict() == {
        "component": "c",
        "severity": "info",
        "message": "m",
        "fix": None,
        "rule_name": "r",
        "evidence": {"k": 1},
    }
