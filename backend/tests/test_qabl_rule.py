# -*- coding: utf-8 -*-
"""V5T-9 and V5T-10 — «من قبل» as the fourth rule, and the three older ones.

v5 joins the registry the same way v4 did: a `find_*_matches` with the sibling
signature, called from `analyze()`, its matches merged and sorted into reading
order. Nothing about the first three rules changes.

**But v5 is NOT a lemma rule, and the model short-circuit had to learn that.**
`LEMMA_RULE_KEYS` is untouched and still `("tam_trigger_lex", "qam")` — «من قبل»
is a *surface* pair, findable without the disambiguator exactly like بشكل. So
`analyze` gained `has_qabl_candidate`, a model-free pre-check, rather than a
fourth entry in the lemma tuple.

**That pre-check uses `endswith`, and the reason is measured.** CAMeL reads
`ومن` and `فمن` as `prep` with `lex == "من"`, so `is_qabl_trigger` fires on
them — «تمت المراجعة **ومن قبل المشرف**» is a real flag. An equality test on the
surface would have been narrower than the trigger it guards and would have
dropped those silently, which is the one direction this rule may not fail in. A
pre-check must never be narrower than the thing it gates.

No test in this file reads anything from `doc/` — the sentences are inline.
"""
import pytest
from unittest.mock import patch

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import (
    LEMMA_RULE_KEYS,
    analyze,
    find_qabl_matches,
    has_qabl_candidate,
)
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)
QABL_RULE_ID = RULES["qabl"]["rule_id"]


def run(text):
    return analyze(rules_path, whitelist_path, text)


def rules_of(text):
    return [match["rule"] for match in run(text)["matches"]]


def phrases_of(text, rule=QABL_RULE_ID):
    return [m["flagged_phrase"] for m in run(text)["matches"] if m["rule"] == rule]


""" V5T-9 — the fourth rule fires """


def test_an_agent_phrase_comes_back_as_a_qabl_match():
    result = run("تمت مراجعة الملف من قبل المشرف")
    assert result["flagged"] is True
    assert QABL_RULE_ID in [match["rule"] for match in result["matches"]]


def test_the_match_carries_an_explanation_and_a_suggestion():
    match = [m for m in run("صدر القرار من قبل الوزارة")["matches"]
             if m["rule"] == QABL_RULE_ID][0]
    assert match["explanation"]
    assert match["suggestion"]
    assert set(match) == {"rule", "flagged_phrase", "explanation", "suggestion"}


def test_the_flagged_phrase_spans_the_whole_construction():
    """Bare: «من قبل» plus the مضاف إليه. With a clitic the genitive is already
    inside the head, so the phrase is two tokens, not three."""
    assert phrases_of("تمت مراجعة الملف من قبل المشرف") == ["من قبل المشرف"]
    assert phrases_of("تحظى بتقدير واحترام من قبلنا") == ["من قبلنا"]


def test_a_temporal_phrase_produces_no_match():
    assert rules_of("كان قد زار المدينة من قبل") == []


def test_the_conjunction_prefixed_form_still_flags():
    """ومن reads `prep`/`من`, so the trigger fires — and the phrase keeps the و
    because that is the surface the reader will look for."""
    assert phrases_of("تمت المراجعة ومن قبل المشرف أيضا") == ["ومن قبل المشرف"]


def test_two_occurrences_in_one_sentence_are_judged_separately():
    """From the labelled set (rows 69–70): «ورد الليكود من قبل على تقارير …
    ممن شغلوا المنصب من قبله». The bare one is temporal and silent, the clitic
    one flags. One match, not one verdict for the sentence."""
    text = "ورد الليكود من قبل على تقارير ممن شغلوا المنصب من قبله"
    assert phrases_of(text) == ["من قبله"]


def test_two_flagging_occurrences_both_report():
    text = "صدر القرار من قبل الوزارة ونفذ من قبل اللجنة"
    assert len(phrases_of(text)) == 2


""" V5T-9 — configuration """


def test_the_rule_is_skipped_when_its_block_is_absent():
    """A v1/v2/v4-only config keeps working, same guarantee v4 gave v1/v2."""
    rules = {key: value for key, value in RULES.items() if key != "qabl"}
    assert find_qabl_matches(rules, WHITELIST, [(0, "من"), (1, "قبل")], [{}, {}]) == []


def test_the_rule_reads_nothing_from_the_whitelist():
    """v5 is the one rule with no override list. Passing an EMPTY whitelist must
    change nothing — if this ever fails, a word list has crept in."""
    text = "تمت مراجعة الملف من قبل المشرف"
    with patch("app.engine.rule_engine.reader", side_effect=[RULES, {}]):
        with_empty = analyze(rules_path, whitelist_path, text)
    assert [m for m in with_empty["matches"] if m["rule"] == QABL_RULE_ID] == \
           [m for m in run(text)["matches"] if m["rule"] == QABL_RULE_ID]


def test_the_rule_id_comes_from_data_not_python():
    rules = dict(RULES)
    rules["qabl"] = dict(RULES["qabl"], rule_id="سمّه ما شئت")
    tokens = [(0, "صدر"), (1, "القرار"), (2, "من"), (3, "قبل"), (4, "الوزارة")]
    disambiguated = [
        {"pos": "verb", "lex": "صدر"}, {"pos": "noun", "lex": "قرار"},
        {"pos": "prep", "lex": "من"}, {"pos": "noun", "lex": "قبل"},
        {"pos": "noun", "lex": "وزارة"},
    ]
    matches = find_qabl_matches(rules, WHITELIST, tokens, disambiguated)
    assert [m["rule"] for _, m in matches] == ["سمّه ما شئت"]


""" V5T-9 — the short-circuit knows v5 is a surface rule, not a lemma rule """


def test_qabl_is_not_in_the_lemma_registry():
    """It is findable without the model, like بشكل — so it does not belong in
    the tuple that means "this rule needs the disambiguator to see anything"."""
    assert LEMMA_RULE_KEYS == ("tam_trigger_lex", "qam")
    assert "qabl" not in LEMMA_RULE_KEYS


@pytest.mark.parametrize(
    "words, expected",
    [
        (["صدر", "من", "قبل", "الوزارة"], True),
        (["صدر", "ومن", "قبل", "الوزارة"], True),
        (["صدر", "من", "قبلنا"], True),
        (["صدر", "القرار", "أمس"], False),
        (["قبل", "الظهر", "من", "الوزارة"], False),
        (["من"], False),
    ],
)
def test_the_pre_check_finds_the_surface_pair_without_the_model(words, expected):
    tokens = list(enumerate(words))
    assert has_qabl_candidate(RULES, tokens) is expected


def test_the_pre_check_is_never_narrower_than_the_trigger():
    """ومن/فمن read `prep`/`من`, so the trigger reaches them. A pre-check that
    did not would silence a real flag before the model ever ran."""
    for prefixed in ["ومن", "فمن"]:
        assert has_qabl_candidate(RULES, [(0, prefixed), (1, "قبل"), (2, "الوزارة")])


def test_the_pre_check_is_off_when_the_block_is_absent():
    rules = {key: value for key, value in RULES.items() if key != "qabl"}
    assert has_qabl_candidate(rules, [(0, "من"), (1, "قبل")]) is False


""" V5T-10 — the three older rules are untouched """


@pytest.mark.parametrize(
    "text, expected",
    [
        ("كتب المقال بشكل رائع", ["بشكل"]),
        ("تم إغلاق الباب", ["تم"]),
        ("قام الباحث بدراسة الظاهرة", ["قام بـ"]),
        ("اشترى خاتم الذهب", []),
        ("بشكل الهرم بنيت القاعة", []),
        ("تم خروج الفريق", []),
        # FLAG, not silent: عملية/حملة were removed from `result_nouns` on
        # 2026-08-28 because a collocation verb exists (أجرى عمليةً)، and the
        # gold sets were relabelled to match. CLAUDE.md said otherwise until
        # V5T-10; the code was right.
        ("قام الجيش بعملية إنقاذ", ["قام بـ"]),
        ("قام المدير بمسؤولياته كاملة", []),
    ],
)
def test_the_older_rules_behave_exactly_as_before(text, expected):
    """Sentences taken from v1/v2/v4's own recorded behaviour. Adding a fourth
    rule must not move any of them — in either direction."""
    assert rules_of(text) == expected


def test_a_sentence_with_two_rules_reports_both_in_reading_order():
    assert rules_of("تمت مراجعة الملف من قبل المشرف") == ["تم", "من قبل"]


def test_a_sentence_with_three_rules_reports_all_three_in_reading_order():
    """تم at token 0, بشكل at 3, من قبل at 5 — the sort is on position, not on
    which finder ran first."""
    assert rules_of("تمت مراجعة الملف بشكل كامل من قبل المشرف") == [
        "تم",
        "بشكل",
        "من قبل",
    ]


def test_clean_text_stays_clean():
    assert run("الجو جميل اليوم") == {"flagged": False, "matches": []}


def test_every_match_declares_which_rule_fired():
    """US: a client must be able to tell the four rules apart."""
    result = run("تمت مراجعة الملف بشكل كامل من قبل المشرف")
    ids = {match["rule"] for match in result["matches"]}
    assert ids <= {
        RULES["bshakl_rule_id"],
        RULES["tam_rule_id"],
        RULES["qam"]["rule_id"],
        RULES["qabl"]["rule_id"],
    }
    assert len(ids) == 3
