# -*- coding: utf-8 -*-
"""V4-7 — three rules in one engine, and the short-circuit that must survive."""
from unittest.mock import patch

import pytest

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import LEMMA_RULE_KEYS, analyze, find_qam_matches
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)


def _whitelist():
    return dict(WHITELIST)


""" the model short-circuit — the main cost saving in the pipeline """


def test_the_registry_lists_every_lemma_triggered_rule():
    """بشكل is deliberately absent: it is a surface scan, which is what lets
    analyze skip the model."""
    assert LEMMA_RULE_KEYS == ("tam_trigger_lex", "qam")


def test_analyze_skips_the_model_when_no_rule_can_have_a_candidate():
    """No بشكل in the text, and neither lemma rule configured."""
    rules = {"trigger_word": "بشكل"}
    tokens = [(0, "الجو"), (1, "جميل")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context"
    ) as disambiguator:
        result = analyze(rules_path, whitelist_path, "الجو جميل")

    assert result == {"flagged": False, "matches": []}
    disambiguator.assert_not_called()


@pytest.mark.parametrize("key", LEMMA_RULE_KEYS)
def test_analyze_runs_the_model_when_any_lemma_rule_is_configured(key):
    """Each lemma rule on its own is enough to require the disambiguator —
    adding a third rule must not let the short-circuit swallow it."""
    value = {"trigger_lex": ["قام"]} if key == "qam" else "تم"
    rules = {"trigger_word": "بشكل", key: value}
    tokens = [(0, "الجو"), (1, "جميل")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context", return_value=[{}, {}]
    ) as disambiguator, patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_qam_matches", return_value=[]
    ):
        analyze(rules_path, whitelist_path, "الجو جميل")

    disambiguator.assert_called_once()


def test_analyze_merges_three_rules_in_reading_order():
    rules = {
        "trigger_word": "بشكل",
        "tam_trigger_lex": "تم",
        "qam": {"trigger_lex": ["قام"]},
    }
    tokens = list(enumerate(["قام", "بدراسة", "تم", "إغلاق", "بشكل", "رائع"]))

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[{}] * len(tokens),
    ), patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[(4, "BSHAKL")]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[(2, "TAM")]
    ), patch(
        "app.engine.rule_engine.find_qam_matches", return_value=[(0, "QAM")]
    ):
        result = analyze(rules_path, whitelist_path, "…")

    assert result == {"flagged": True, "matches": ["QAM", "TAM", "BSHAKL"]}


""" find_qam_matches — self-gating and the mechanical branches """


def test_find_qam_matches_is_off_without_its_config_key():
    """A v1/v2-only rules.json keeps working unchanged."""
    assert find_qam_matches({}, _whitelist(), [(0, "قام")], [{}]) == []


def test_find_qam_matches_flags_a_surviving_candidate():
    """Since the Case 3/4 reopening, a candidate that survives Cases 1/2/5 and
    is not a listed result noun FLAGS — the abstain state is gone."""
    from app.engine.analysis import get_pos_and_pattern_in_context
    from app.text.preprocessor import preprocess

    tokens = preprocess("قام الباحث بدراسة الظاهرة")
    entries = get_pos_and_pattern_in_context(tokens)

    assert [m["flagged_phrase"] for _, m in
            find_qam_matches(RULES, WHITELIST, tokens, entries)] == ["قام بدراسة"]


""" v4 must not disturb v1 or v2 """


@pytest.mark.parametrize(
    "sentence, phrases",
    [
        ("كتب المقال بشكل جميل", ["بشكل جميل"]),
        ("تم إغلاق الباب", ["تم إغلاق"]),
        ("تم التدقيق والمراجعة", []),
        ("اشترى خاتم الذهب", []),
        ("قام الباحث بدراسة الظاهرة", ["قام بدراسة"]),
        ("قام الباحث بدراسة الظاهرة بشكل جيد", ["قام بدراسة", "بشكل جيد"]),
    ],
)
def test_real_analyze_with_all_three_rules_live(sentence, phrases):
    result = analyze(rules_path, whitelist_path, sentence)

    assert [m["flagged_phrase"] for m in result["matches"]] == phrases
