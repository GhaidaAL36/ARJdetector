# -*- coding: utf-8 -*-
"""V5T-12 — every match says which rule fired, and the name comes from `data/`.

There is no new code in this task and that is the point: `build_match` already
takes `rule_id` as an argument, and all four ids already live in
`data/rules.json`. What was missing is proof — that the field survives to the
API answer, and that it is genuinely read from config rather than a Python
literal that happens to match.

The proof is behavioural, not textual: each rule's id is **changed in the
config** and the response is required to change with it. Grepping the source for
the Arabic strings would not work anyway — `get_suggestion` contains «بشكل» and
`get_tam_suggestion` contains «تم» as ordinary prose.

No test in this file reads anything from `doc/`.
"""
import inspect

import pytest
from unittest.mock import patch

from app.config import rules_path, whitelist_path
from app.engine.match import build_match
from app.engine.rule_engine import analyze
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)

#: rule -> (a sentence that fires it, its configured id, how to rename it)
FIRES = {
    "بشكل": ("كتب المقال بشكل رائع", RULES["bshakl_rule_id"]),
    "تم": ("تم إغلاق الباب", RULES["tam_rule_id"]),
    "قام بـ": ("قام الباحث بدراسة الظاهرة", RULES["qam"]["rule_id"]),
    "من قبل": ("صدر القرار من قبل الوزارة", RULES["qabl"]["rule_id"]),
}


def renamed(rules, rule, new_id):
    rules = {key: dict(value) if isinstance(value, dict) else value
             for key, value in rules.items()}
    if rule == "بشكل":
        rules["bshakl_rule_id"] = new_id
    elif rule == "تم":
        rules["tam_rule_id"] = new_id
    elif rule == "قام بـ":
        rules["qam"]["rule_id"] = new_id
    else:
        rules["qabl"]["rule_id"] = new_id
    return rules


def without_id(rules, rule):
    rules = {key: dict(value) if isinstance(value, dict) else value
             for key, value in rules.items()}
    if rule == "بشكل":
        rules.pop("bshakl_rule_id")
    elif rule == "تم":
        rules.pop("tam_rule_id")
    elif rule == "قام بـ":
        rules["qam"].pop("rule_id")
    else:
        rules["qabl"].pop("rule_id")
    return rules


def rules_reported(text, rules=None):
    if rules is None:
        return [m["rule"] for m in analyze(rules_path, whitelist_path, text)["matches"]]
    with patch("app.engine.rule_engine.reader", side_effect=[rules, dict(WHITELIST)]):
        return [m["rule"] for m in analyze(rules_path, whitelist_path, text)["matches"]]


""" the field is there, on every match """


@pytest.mark.parametrize("rule", sorted(FIRES))
def test_each_rule_names_itself_when_it_fires(rule):
    text, rule_id = FIRES[rule]
    assert rule_id in rules_reported(text)


def test_every_match_carries_the_field_and_nothing_extra():
    text = "تمت مراجعة الملف بشكل كامل من قبل المشرف"
    for match in analyze(rules_path, whitelist_path, text)["matches"]:
        assert set(match) == {"rule", "flagged_phrase", "explanation", "suggestion"}
        assert match["rule"]


def test_the_four_ids_are_distinct():
    """A client tells the rules apart by this string, so two rules sharing one
    would be undetectable in the response."""
    ids = [rule_id for _, rule_id in FIRES.values()]
    assert len(set(ids)) == 4, ids


""" the name comes from data/, not from Python """


def test_build_match_cannot_be_called_without_a_rule_id():
    """Structural guarantee: no default, so a fifth rule cannot quietly emit
    matches with a missing or invented name."""
    parameter = inspect.signature(build_match).parameters["rule_id"]
    assert parameter.default is inspect.Parameter.empty


@pytest.mark.parametrize("rule", sorted(FIRES))
def test_renaming_a_rule_in_config_renames_it_in_the_answer(rule):
    """THE REAL PROOF. If the id were hardcoded in Python this would fail."""
    text, original = FIRES[rule]
    reported = rules_reported(text, renamed(RULES, rule, "اسم-جديد"))
    assert "اسم-جديد" in reported
    assert original not in reported


@pytest.mark.parametrize(
    "rule, fallback",
    [("بشكل", "بشكل"), ("تم", "تم"), ("قام بـ", "قام"), ("من قبل", "من قبل")],
)
def test_a_rule_falls_back_to_its_own_trigger_when_the_id_is_absent(rule, fallback):
    """A config predating the `rule_id` key keeps working, and the name it gets
    is the trigger — which is exactly what these were hardcoded to before
    V4-8 moved them into `data/`."""
    text, _ = FIRES[rule]
    assert fallback in rules_reported(text, without_id(RULES, rule))


""" and it survives to the API answer """


def test_the_endpoint_returns_the_rule_for_every_match():
    """`main.py` declares no response model, so the dict passes through — but
    that is a property worth pinning rather than assuming, since adding one
    later would silently strip the field."""
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).post(
        "/analyze", json={"text": "تمت مراجعة الملف بشكل كامل من قبل المشرف"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["flagged"] is True
    assert [match["rule"] for match in body["matches"]] == ["تم", "بشكل", "من قبل"]


def test_the_endpoint_returns_an_empty_match_list_for_clean_text():
    from fastapi.testclient import TestClient

    from app.main import app

    body = TestClient(app).post("/analyze", json={"text": "الجو جميل اليوم"}).json()
    assert body == {"flagged": False, "matches": []}
