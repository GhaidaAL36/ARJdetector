# -*- coding: utf-8 -*-
"""V5T-11 — the disambiguator must not be built for text no rule can match.

Loading and running the MLE model is the expensive step in the pipeline, so
`analyze` refuses to construct it when nothing could possibly fire. v4 pinned
that with a test parametrized over the rule registry, so a new rule could not be
added without extending it. v5 is the new rule.

**But v5 does not go in `LEMMA_RULE_KEYS`, and that is the point of this task.**
The registry splits rules by *how they are found*, not by how many there are:

    lemma-gated   تم، قام بـ    the trigger IS an analysis — the model must run
                                before we can know whether a candidate exists
    surface-gated بشكل، من قبل   the trigger is visible in the raw token list,
                                so the text itself decides

Putting `qabl` in the lemma tuple would say "any text whatsoever needs the
model whenever this rule is configured", which is false and would throw away the
saving for every بشكل-free sentence. It is gated by `has_qabl_candidate`
instead.

`test_every_rule_in_data_is_classified` is the guard the task actually asks for:
a fifth rule added to `data/rules.json` fails it until someone says which half
it belongs to.

No test in this file reads anything from `doc/`.
"""
import pytest
from unittest.mock import patch

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import LEMMA_RULE_KEYS, analyze, has_qabl_candidate
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)

#: Findable in the raw token list, so the text decides whether the model runs.
SURFACE_RULE_KEYS = ("trigger_word", "qabl")

QABL_SPEC = RULES["qabl"]

#: key -> (config for that rule alone, tokens that let it have a candidate)
RULE_GATES = {
    "tam_trigger_lex": ("تم", ["الجو", "جميل"]),
    "qam": ({"trigger_lex": ["قام"]}, ["الجو", "جميل"]),
    "trigger_word": ("بشكل", ["كتب", "بشكل", "رائع"]),
    "qabl": (QABL_SPEC, ["صدر", "من", "قبل", "الوزارة"]),
}


def run_with(rules, words):
    """analyze() with every finder stubbed — this measures the gate, not the
    rules. Returns the disambiguator mock so a test can assert on it."""
    tokens = list(enumerate(words))
    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, dict(WHITELIST)]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[{}] * len(tokens),
    ) as disambiguator, patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_qam_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_qabl_matches", return_value=[]
    ):
        analyze(rules_path, whitelist_path, " ".join(words))
    return disambiguator


""" the registry covers every rule """


def test_every_rule_in_data_is_classified():
    """THE GUARD. Every key in `data/rules.json` is either a rule that needs the
    model to find its trigger, a rule findable on the surface, or a `rule_id`
    label. A fifth rule cannot appear without a decision being made here."""
    classified = set(LEMMA_RULE_KEYS) | set(SURFACE_RULE_KEYS)
    unclassified = {
        key for key in RULES if key not in classified and not key.endswith("rule_id")
    }
    assert unclassified == set(), unclassified


def test_qabl_is_surface_gated_not_lemma_gated():
    """«من قبل» is two ordinary tokens; بشكل is one. Neither needs the model to
    know whether it *might* match, which is exactly what the lemma tuple means.
    """
    assert "qabl" in SURFACE_RULE_KEYS
    assert "qabl" not in LEMMA_RULE_KEYS
    assert LEMMA_RULE_KEYS == ("tam_trigger_lex", "qam")


""" the model runs when — and only when — a rule can have a candidate """


@pytest.mark.parametrize("key", sorted(RULE_GATES))
def test_the_model_runs_when_a_rule_can_have_a_candidate(key):
    value, words = RULE_GATES[key]
    rules = {"trigger_word": "بشكل", key: value}
    run_with(rules, words).assert_called_once()


def test_the_model_is_skipped_when_nothing_is_configured():
    run_with({"trigger_word": "بشكل"}, ["الجو", "جميل"]).assert_not_called()


def test_the_model_is_skipped_when_qabl_is_configured_but_absent_from_the_text():
    """The v5 half of the saving. Configuring the rule is not enough — «من قبل»
    has to actually be in the sentence."""
    rules = {"trigger_word": "بشكل", "qabl": QABL_SPEC}
    run_with(rules, ["الجو", "جميل", "اليوم"]).assert_not_called()


@pytest.mark.parametrize(
    "words",
    [
        ["زرت", "المدينة", "قبل", "أسبوع"],   # قبل with no من
        ["وصلت", "من", "الوزارة", "أمس"],      # من with no قبل
        ["قبل", "الظهر", "وصلت", "من"],        # both words, wrong order
    ],
)
def test_a_half_pair_does_not_wake_the_model(words):
    """«من قبلة المسجد» is deliberately NOT here — the pre-check is wider than
    the trigger, so it wakes the model and `_is_qabl_head` rejects it after.
    See `test_the_pre_check_is_allowed_to_be_wider_than_the_trigger`."""
    rules = {"trigger_word": "بشكل", "qabl": QABL_SPEC}
    run_with(rules, words).assert_not_called()


def test_the_pre_check_is_allowed_to_be_wider_than_the_trigger():
    """«من قبلة المسجد» is NOT this construction — `_is_qabl_head` rejects قبلة.
    But the pre-check only asks "is it worth looking", so being wider is free
    and being narrower is a silent miss. `startswith` here, exact match there.
    """
    assert has_qabl_candidate(RULES, list(enumerate(["من", "قبلة"]))) is True
    assert has_qabl_candidate(RULES, list(enumerate(["من", "قبل"]))) is True


""" what the saving is actually worth, with the shipped config """


def test_the_shipped_config_always_needs_the_model():
    """Honest accounting: `data/rules.json` configures تم and قام بـ, which are
    lemma-gated, so the short-circuit never fires in production and
    `has_qabl_candidate` buys no speed there.

    It is a CORRECTNESS guard, not a performance one — without it, a config
    carrying only بشكل and قبل would skip the model and silently drop every
    «من قبل» match. That is the case the test above pins.
    """
    assert any(RULES.get(key) for key in LEMMA_RULE_KEYS)
    run_with(dict(RULES), ["الجو", "جميل"]).assert_called_once()


def test_removing_the_lemma_rules_makes_the_qabl_gate_load_bearing():
    """Same text, two configs: with تم/قام present the model runs regardless;
    with only the surface rules it runs if and only if «من قبل» is there."""
    surface_only = {"trigger_word": "بشكل", "qabl": QABL_SPEC}
    run_with(surface_only, ["الجو", "جميل"]).assert_not_called()
    run_with(surface_only, ["صدر", "من", "قبل", "الوزارة"]).assert_called_once()
