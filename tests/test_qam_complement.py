# -*- coding: utf-8 -*-
import csv
import io

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_qam_trigger
from app.engine.rule_engine import QAM_MAX_SKIP_TOKENS, qam_complement_index
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

QAM_TRIGGER_LEXES = reader(rules_path)["qam"]["trigger_lex"]
QAM_MISTAGGED = reader(whitelist_path)["qam"]["mistagged_surfaces"]

""" qam_complement_index — unit tests, no CAMeL """


def build(*words):
    """words are (surface, pos, prc1) triples."""
    tokens = [(i, w) for i, (w, _, _) in enumerate(words)]
    disambiguated = [
        {"pos": pos, "prc1": prc1, "lex": w, "pattern": "", "prc0": "0", "prc2": "0"}
        for w, pos, prc1 in words
    ]
    return tokens, disambiguated


def scan(index, *words, max_skip=QAM_MAX_SKIP_TOKENS):
    tokens, disambiguated = build(*words)
    return qam_complement_index(tokens, index, disambiguated, max_skip)


def test_finds_an_adjacent_complement():
    """«قام بدوره في المشروع» — no agent, so the complement is at index + 1."""
    assert scan(0, ("قام", "verb", "0"), ("بدوره", "noun", "bi_prep")) == 1


def test_scans_past_the_agent():
    """The whole point — checking index + 1 alone finds nothing here."""
    assert scan(
        0, ("قام", "verb", "0"), ("الباحث", "noun", "0"), ("بدراسة", "noun", "bi_prep")
    ) == 2


def test_takes_the_first_complement_not_a_later_one():
    assert scan(
        0,
        ("قام", "verb", "0"),
        ("بدراسة", "noun", "bi_prep"),
        ("بمراجعة", "noun", "bi_prep"),
    ) == 1


def test_none_when_there_is_no_complement():
    """«قام الرجل من مكانه» — من is a plain prep token, never prc1."""
    assert scan(
        0, ("قام", "verb", "0"), ("الرجل", "noun", "0"), ("من", "prep", "0")
    ) is None


def test_none_when_the_trigger_is_the_last_token():
    assert scan(1, ("زار", "verb", "0"), ("قم", "verb", "0")) is None


def test_stops_at_sentence_end():
    """The complement must belong to this sentence."""
    assert scan(
        0,
        ("قام", "verb", "0"),
        ("الرجل", "noun", "0"),
        (".", "punc", "0"),
        ("بمراجعة", "noun", "bi_prep"),
    ) is None


def test_does_not_stop_at_a_verb():
    """CAMeL tags علم in «في علم الاجتماع» as a verb. A verb-stop would abort
    mid-agent and lose a correct flag, so only punctuation stops the scan."""
    assert scan(
        0,
        ("قام", "verb", "0"),
        ("الباحث", "noun", "0"),
        ("في", "prep", "0"),
        ("علم", "verb", "0"),
        ("الاجتماع", "noun", "0"),
        ("بدراسة", "noun", "bi_prep"),
    ) == 5


def test_reaches_the_measured_maximum_gap():
    words = [("قام", "verb", "0")] + [("x", "noun", "0")] * 5
    words.append(("بدراسة", "noun", "bi_prep"))

    assert scan(0, *words) == 6


def test_gives_up_beyond_the_skip_limit():
    words = [("قام", "verb", "0")] + [("x", "noun", "0")] * 6
    words.append(("بدراسة", "noun", "bi_prep"))

    assert scan(0, *words) is None


def test_the_limit_is_a_parameter():
    words = (
        ("قام", "verb", "0"),
        ("الباحث", "noun", "0"),
        ("بدراسة", "noun", "bi_prep"),
    )

    assert scan(0, *words, max_skip=1) is None
    assert scan(0, *words, max_skip=2) == 2


""" against real CAMeL, over the labelled set """


def complement_of(sentence):
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qam_trigger(tokens, index, disambiguated, QAM_TRIGGER_LEXES, QAM_MISTAGGED):
            found = qam_complement_index(tokens, index, disambiguated)
            return None if found is None else tokens[found][1]
    return None


def labelled_rows():
    with io.open("doc/labelled_set.csv", encoding="utf-8-sig") as handle:
        return [row for row in csv.DictReader(handle) if row.get("sentence")]


BI_PREP_ROWS = [r for r in labelled_rows() if r["gold"] == "bi_prep"]
NO_MATCH_ROWS = [r for r in labelled_rows() if r["gold"] == "NO-TRIGGER"]


@pytest.mark.parametrize(
    "row", BI_PREP_ROWS, ids=[r["sentence"][:28] for r in BI_PREP_ROWS]
)
def test_real_finds_the_complement_recorded_in_the_labelled_set(row):
    """The 10 real bi_prep cases from test_prc1.py, at the index it recorded."""
    tokens = preprocess(row["sentence"])
    expected = tokens[int(row["note"].split()[1])][1]

    assert complement_of(row["sentence"]) == expected


@pytest.mark.parametrize(
    "row", NO_MATCH_ROWS, ids=[r["sentence"][:28] for r in NO_MATCH_ROWS]
)
def test_real_non_light_verb_senses_resolve_no_complement(row):
    """قام من / قامت بين / يقوم على — the trigger fires, but there is no
    bi_prep, so the scan returns None and no match can form."""
    assert complement_of(row["sentence"]) is None


@pytest.mark.parametrize(
    "sentence, expected",
    [
        ("قام وزير الخارجية السعودي بزيارة المصنع", "بزيارة"),
        ("قام رئيس اللجنة الوطنية للانتخابات بمراجعة النتائج", "بمراجعة"),
        ("قامت وزيرة الشؤون الاجتماعية والعمل بتوزيع المساعدات", "بتوزيع"),
        ("قام الباحث المتخصص في علم الاجتماع بدراسة الظاهرة", "بدراسة"),
    ],
)
def test_real_reaches_past_a_long_agent(sentence, expected):
    """A limit of 3 drops every one of these — long-titled subjects are exactly
    the register this rule targets."""
    assert complement_of(sentence) == expected


def test_real_the_stem_initial_ba_sentences_have_no_complement():
    """بحثا، بيان، بناء… read prc1 == 0, so they are never mistaken for بـ."""
    for row in labelled_rows():
        if row["gold"] == "not-bi_prep":
            assert complement_of(row["sentence"]) is None
