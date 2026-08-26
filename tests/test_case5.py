# -*- coding: utf-8 -*-
import csv
import io

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_described_complement, is_qam_trigger
from app.engine.rule_engine import qam_complement_index
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

LEXES = reader(rules_path)["qam"]["trigger_lex"]
MISTAGGED = reader(whitelist_path)["qam"]["mistagged_surfaces"]

""" is_described_complement — unit tests, no CAMeL """


def disambiguated(*poses):
    return [{"pos": pos, "prc1": "0", "lex": "", "pattern": "", "prc0": "0", "prc2": "0"}
            for pos in poses]


def test_adjective_after_the_complement_is_case_five():
    """«قامت الحكومة بإصلاح شامل» — nothing for the collapsed verb to take."""
    assert is_described_complement(disambiguated("verb", "noun", "noun", "adj"), 2) is True


def test_noun_after_the_complement_is_not_case_five():
    """«قام الفني بإصلاح الجهاز» — collapses cleanly, must stay flaggable."""
    assert is_described_complement(disambiguated("verb", "noun", "noun", "noun"), 2) is False


def test_preposition_after_the_complement_is_not_case_five():
    """«قام الوفد بجولة في المدينة» — في is prep, and the sentence is عرنجي."""
    assert is_described_complement(disambiguated("verb", "noun", "noun", "prep"), 2) is False


def test_complement_at_the_end_is_not_case_five():
    """«قام الجيش بالعملية» — no modifier at all; falls through to the table."""
    assert is_described_complement(disambiguated("verb", "noun", "noun"), 2) is False


def test_only_the_token_immediately_after_counts():
    """An adjective further along modifies something else."""
    assert is_described_complement(disambiguated("verb", "noun", "noun", "adj"), 1) is False


""" against real CAMeL """


def rows(path):
    with io.open(path, encoding="utf-8-sig") as handle:
        return [row for row in csv.DictReader(handle)]


def case_five_fires(sentence):
    tokens = preprocess(sentence)
    entries = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qam_trigger(tokens, index, entries, LEXES, MISTAGGED):
            complement = qam_complement_index(tokens, index, entries)
            if complement is None:
                return None
            return is_described_complement(entries, complement)
    return None


LABELLED = [r for r in rows("doc/labelled_set.csv") if r.get("sentence")]
CASE_5_ROWS = [r for r in LABELLED if r["case"] == "Case 5"]
FLAG_ROWS = [r for r in LABELLED if r["gold"] == "FLAG"]
GRID = [r for r in rows("doc/context_test.csv") if r.get("الجملة")]


@pytest.mark.parametrize(
    "row",
    [r for r in CASE_5_ROWS if r["next_pos"] == "adj"],
    ids=[r["sentence"][:26] for r in CASE_5_ROWS if r["next_pos"] == "adj"],
)
def test_real_catches_the_adjective_complements_in_the_labelled_set(row):
    assert case_five_fires(row["sentence"]) is True


def test_real_misses_the_case_five_row_camel_mistags():
    """«قامت الوزارة بخطوة استباقية» — استباقية is an adjective that CAMeL
    returns as noun, so Case 5 cannot see it. Documented, not fixed: see
    test_real_analyzer_backstop_is_a_net_loss."""
    assert case_five_fires("قامت الوزارة بخطوة استباقية") is False


@pytest.mark.parametrize(
    "row", FLAG_ROWS, ids=[r["sentence"][:26] for r in FLAG_ROWS]
)
def test_real_never_silences_a_flag_row(row):
    """The standing invariant — zero missed عرنجية."""
    assert case_five_fires(row["sentence"]) is not True


def test_real_measured_on_the_context_grid():
    """12 correct silences, 0 wrong, matching the V4-27 first pass."""
    right = wrong = 0
    for row in GRID:
        if case_five_fires(row["الجملة"]):
            if row["حكمي (راجعيه)"].strip() == "فصيح":
                right += 1
            else:
                wrong += 1

    assert (right, wrong) == (12, 0)


def test_real_agrees_with_the_grids_own_adjective_column():
    """context_test.csv records which rows the adjective rule should silence."""
    for row in GRID:
        expected = row["قاعدة الصفة"].strip() == "صامت"
        assert bool(case_five_fires(row["الجملة"])) is expected, row["الجملة"]


def test_real_analyzer_backstop_is_a_net_loss():
    """RULED OUT — do not re-try. The task suggested checking a lower-ranked
    CAMeL analysis for the adj reading the top one misses.

    The MLE disambiguator returns exactly one analysis per word, so there is no
    lower rank to consult there. The standalone Analyzer does return many, but
    accepting "any analysis is adj" recovers only منزلية of the four mistags
    while OPENING wrong silences: العملية and المصنع both carry an adj analysis,
    so «قامت القوات بتنفيذ العملية» and «قام الوزير بزيارة المصنع» would be
    silenced — missed عرنجية, the one direction the invariant forbids.
    """
    from app.engine.analysis import analyze_word

    def with_backstop(sentence):
        tokens = preprocess(sentence)
        entries = get_pos_and_pattern_in_context(tokens)
        for index, _ in tokens:
            if is_qam_trigger(tokens, index, entries, LEXES, MISTAGGED):
                complement = qam_complement_index(tokens, index, entries)
                if complement is None:
                    return None
                if is_described_complement(entries, complement):
                    return True
                after = complement + 1
                if after < len(tokens):
                    return any(a.get("pos") == "adj" for a in analyze_word(tokens[after][1]))
                return False
        return None

    right = wrong = 0
    for row in GRID:
        if with_backstop(row["الجملة"]):
            if row["حكمي (راجعيه)"].strip() == "فصيح":
                right += 1
            else:
                wrong += 1

    assert (right, wrong) == (13, 4), "backstop behaviour changed — re-read the docstring"
