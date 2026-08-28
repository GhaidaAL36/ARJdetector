# -*- coding: utf-8 -*-
"""Cases 3/4 — the explicit rule engine that replaced the offline build step.

REOPENED 2026-08-27 after four offline mechanisms failed to separate event from
result (corpus attestation, absolute PLL, contrastive PLL, LM semantic judge).
See the decision record in CLAUDE.md.

**These numbers are a FIT, not a held-out measurement.** The result-noun list was
derived from these same two files, so this is training accuracy. V4-17's held-out
eval is the real test.
"""
import csv
import io

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_result_noun
from app.engine.rule_engine import analyze
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

RULE_ID = reader(rules_path)["qam"]["rule_id"]
RESULT_NOUNS = reader(whitelist_path)["qam"]["result_nouns"]


def qam_flags(sentence):
    return any(m["rule"] == RULE_ID
               for m in analyze(rules_path, whitelist_path, sentence)["matches"])


""" is_result_noun — unit """


def entries(*lexes):
    return [{"lex": lex, "pos": "noun", "prc0": "0", "prc1": "0", "prc2": "0",
             "pattern": ""} for lex in lexes]


def test_a_listed_lemma_is_a_result_noun():
    assert is_result_noun(entries("قام", "عملية"), 1, ["عملية"]) is True


def test_an_unlisted_lemma_is_not():
    assert is_result_noun(entries("قام", "دراسة"), 1, ["عملية"]) is False


def test_an_empty_list_never_suppresses():
    """With the list empty the tool still behaves — it just flags more."""
    assert is_result_noun(entries("قام", "عملية"), 1, []) is False


def test_no_complement_is_not_a_result_noun():
    assert is_result_noun(entries("قام"), None, ["عملية"]) is False


""" the two gold sets """


def test_real_labelled_set_is_fully_correct():
    rows = [r for r in csv.DictReader(io.open("doc/labelled_set.csv", encoding="utf-8-sig"))
            if r.get("gold") in ("FLAG", "SILENT", "NO-TRIGGER")]
    wrong = [(r["gold"], r["sentence"]) for r in rows
             if qam_flags(r["sentence"]) != (r["gold"] == "FLAG")]

    assert wrong == []
    assert len(rows) == 31


def test_real_context_grid_has_zero_missed_arnajiyya():
    """THE STANDING INVARIANT. A false flag is visible and arguable; a missed
    flag is invisible and the writer never learns the tool had nothing to say."""
    missed = []
    for r in csv.DictReader(io.open("doc/context_test.csv", encoding="utf-8-sig")):
        if not r.get("الجملة"):
            continue
        if r["حكمك"].strip() == "عرنجي" and not qam_flags(r["الجملة"]):
            missed.append(r["الجملة"])

    assert missed == []


def test_real_context_grid_has_exactly_one_false_flag():
    """جولة, which V4-27 called 'override-list entry number one'. Both readings
    take a noun complement, so no structural test separates them. Recorded as a
    false FLAG — the allowed direction — rather than listed, which would silence
    «قام الوفد بجولة في المدينة»."""
    false_flags = [r["الجملة"]
                   for r in csv.DictReader(io.open("doc/context_test.csv", encoding="utf-8-sig"))
                   if r.get("الجملة") and r["حكمك"].strip() == "فصيح"
                   and qam_flags(r["الجملة"])]

    assert false_flags == ["قام الطرفان بجولة مفاوضات"]


""" the list is closed, and cannot silence a real flag """


def test_the_result_noun_list_is_the_four_the_gold_data_requires():
    assert sorted(RESULT_NOUNS) == sorted(["واجب", "دور", "عملية", "حملة"])


@pytest.mark.parametrize(
    "sentence", ["قام الجيش بعملية إنقاذ", "قام الموظف بدوره في المشروع",
                 "قامت الشرطة بحملة تفتيش", "قام القائد بواجب الدفاع عن المدينة"]
)
def test_real_each_listed_noun_earns_its_entry(sentence):
    assert qam_flags(sentence) is False


""" the mistagged-adjective list, matched on surface """


@pytest.mark.parametrize(
    "sentence", ["قام الطبيب بزيارة منزلية", "قامت الشركة بخطوة جريئة",
                 "قامت الحكومة بإجراء احترازي", "قامت الوزارة بخطوة استباقية"]
)
def test_real_mistagged_adjectives_reach_case_five(sentence):
    assert qam_flags(sentence) is False


def test_real_the_lemma_behind_a_mistagged_adjective_is_untouched():
    """منزلية lemmatises to منزل, the ordinary noun 'house'. Matching on lex
    would silence this genuine flag; matching on surface does not."""
    assert qam_flags("قام الوزير بزيارة منزل") is True
