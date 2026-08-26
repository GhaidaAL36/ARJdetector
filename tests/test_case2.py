# -*- coding: utf-8 -*-
"""Case 2 — نفي مع أدوات التأكيد. القاعدة row 2."""
import csv
import io

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_emphatic_negation, is_qam_trigger
from app.engine.rule_engine import qam_complement_index
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)
LEXES = RULES["qam"]["trigger_lex"]
EMPHASIS = RULES["qam"]["emphasis_lex"]
MISTAGGED = WHITELIST["qam"]["mistagged_surfaces"]
NEGATION = WHITELIST["qam"]["negation_surfaces"]
EMPHASIS_SURFACES = WHITELIST["qam"]["emphasis_surfaces"]

""" unit tests, no CAMeL """


def build(*words):
    """words are (surface, pos, lex) triples."""
    tokens = [(i, w) for i, (w, _, _) in enumerate(words)]
    entries = [
        {"pos": pos, "lex": lex, "prc0": "0", "prc1": "0", "prc2": "0", "pattern": ""}
        for _, pos, lex in words
    ]
    return tokens, entries


def fires(trigger, complement, *words, emphasis=EMPHASIS, negation=NEGATION,
          surfaces=EMPHASIS_SURFACES):
    tokens, entries = build(*words)
    return is_emphatic_negation(
        tokens, trigger, complement, entries, emphasis, negation, surfaces
    )


NEGATED_ANY = (("لم", "part_neg", "لم"), ("يقم", "verb", "قام"), ("بأي", "noun_quant", "أي"))


def test_negation_plus_emphasis_suppresses():
    assert fires(1, 2, *NEGATED_ANY) is True


def test_emphasis_without_negation_does_not_suppress():
    """«قام بأي إجراء ممكن» — no negation, so the collapse is not blocked."""
    assert fires(0, 1, ("قام", "verb", "قام"), ("بأي", "noun_quant", "أي")) is False


def test_negation_without_emphasis_does_not_suppress():
    """THE V4-6 DECISION. «لم يقم بالدراسة» → «لم يدرس» collapses cleanly."""
    assert fires(
        1, 2, ("لم", "part_neg", "لم"), ("يقم", "verb", "قام"), ("بالدراسة", "noun", "دراسة")
    ) is False


def test_a_trigger_at_the_start_has_no_negation_before_it():
    assert fires(0, 1, ("قام", "verb", "قام"), ("بأي", "noun_quant", "أي")) is False


def test_no_complement_does_not_suppress():
    assert fires(1, None, *NEGATED_ANY) is False


def test_the_surface_negation_list_is_consulted():
    """ما reads pron_rel in every context, so pos alone cannot reach it."""
    words = (("ما", "pron_rel", "ما"), ("قام", "verb", "قام"), ("بأي", "noun_quant", "أي"))

    assert fires(1, 2, *words) is True
    assert fires(1, 2, *words, negation=[]) is False


def test_emphasis_lex_must_match():
    words = (("لم", "part_neg", "لم"), ("يقم", "verb", "قام"), ("بكل", "noun_quant", "كل"))

    assert fires(1, 2, *words) is False


def test_a_plain_noun_complement_is_not_emphasis():
    """pos must be noun_quant — a مصدر named أي-something is not the particle."""
    words = (("لم", "part_neg", "لم"), ("يقم", "verb", "قام"), ("بأي", "noun", "أي"))

    assert fires(1, 2, *words) is False


""" against real CAMeL """


def case_two_fires(sentence):
    tokens = preprocess(sentence)
    entries = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qam_trigger(tokens, index, entries, LEXES, MISTAGGED):
            complement = qam_complement_index(tokens, index, entries)
            return is_emphatic_negation(
                tokens, index, complement, entries, EMPHASIS, NEGATION,
                EMPHASIS_SURFACES,
            )
    return None


@pytest.mark.parametrize(
    "sentence",
    [
        "لم يقم المسؤول بأي إجراء",
        "لن يقوم بأي عمل",
        "لا يقوم بأي جهد",
        "لم تقم الحكومة بأي خطوة",
        "ما قام بأي إجراء",
    ],
)
def test_real_negation_with_emphasis_is_suppressed(sentence):
    assert case_two_fires(sentence) is True


@pytest.mark.parametrize(
    "sentence",
    [
        "لم يقم بالدراسة",
        "لم تقم اللجنة بمراجعة الطلب",
        "لن يقوم الفريق بتحليل البيانات",
    ],
)
def test_real_negation_without_emphasis_still_flags(sentence):
    """RECORDED DECISION (V4-6): negation alone does not suppress, because the
    collapse survives it — «لم يدرس»، «لم تراجع اللجنة الطلب»."""
    assert case_two_fires(sentence) is False


def test_real_the_labelled_set_case_two_row():
    rows = [
        r
        for r in csv.DictReader(io.open("doc/labelled_set.csv", encoding="utf-8-sig"))
        if r.get("case") == "Case 2"
    ]

    assert [r["sentence"] for r in rows] == ["لم يقم المسؤول بأي إجراء"]
    assert case_two_fires(rows[0]["sentence"]) is True


def test_real_never_silences_a_flag_row():
    """The standing invariant — zero missed عرنجية."""
    for row in csv.DictReader(io.open("doc/labelled_set.csv", encoding="utf-8-sig")):
        if row.get("gold") == "FLAG":
            assert case_two_fires(row["sentence"]) is not True, row["sentence"]


@pytest.mark.parametrize(
    "sentence",
    ["لم يقم بأية خطوة", "لم تقم بأية خطوة", "لم يقم بأية إجراءات",
     "ما قامت بأية محاولة"],
)
def test_real_feminine_emphasis_form_is_matched_on_surface(sentence):
    """«لم تقم بأية…» is common. CAMeL gives أية the lex آية ("verse"), so it is
    matched on SURFACE instead — أية (hamza, U+0623)."""
    assert case_two_fires(sentence) is True


def test_real_the_genuine_quranic_noun_is_untouched():
    """آية with madda (U+0622) is a different surface, so the entry cannot
    reach it — and there is no negation before قام here either."""
    assert case_two_fires("استشهد الخطيب بآية كريمة") is None


def test_the_two_spellings_really_do_differ():
    """The whole entry rests on this: same lex, different surface."""
    assert EMPHASIS_SURFACES == ["أية"]
    assert [hex(ord(c)) for c in EMPHASIS_SURFACES[0]][0] == "0x623"
    assert [hex(ord(c)) for c in "آية"][0] == "0x622"


def test_the_surface_list_needs_no_negation_bypass():
    """The surface entry still requires negation — it only replaces the lex
    half of the test, not the negation half."""
    assert fires(0, 1, ("قام", "verb", "قام"), ("بأية", "noun_prop", "آية")) is False


def test_the_rule_still_works_with_the_emphasis_surface_list_empty():
    assert fires(1, 2, *NEGATED_ANY, surfaces=[]) is True


""" the lists live in data/, not in Python """


def test_emphasis_lex_comes_from_rules_json():
    assert EMPHASIS == ["أي"]


def test_the_negation_surface_list_stays_bounded():
    """One entry, for the one particle CAMeL never tags part_neg. لم/لن/لا are
    matched algorithmically and must not be added here."""
    assert NEGATION == ["ما"]


def test_the_rule_still_works_with_the_negation_list_empty():
    assert fires(1, 2, *NEGATED_ANY, negation=[]) is True
