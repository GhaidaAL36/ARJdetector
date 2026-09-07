# -*- coding: utf-8 -*-
"""V5T-5 — finding «من قبل» in the text.

The trigger is **two tokens**, and each half is matched a different way. That
split is the whole content of this task, and it is measured, not assumed:

* **من — lemma + `pos == prep`.** Same shape as v2's `is_tam_trigger` and v4's
  `is_qam_trigger`.
* **قبل — surface.** A lemma test is not merely unreliable here, it is
  *uninformative*. `get_pos_and_pattern_in_context` dediacritizes `lex`, so
  قِبَل ("side"), قَبْلَ ("before") and قَبِلَ ("accepted") all arrive as the same
  string `قبل`. Probed over all twelve persons plus قبلة: **`lex` is `قبل` for
  every one of them.** `pos` does not separate them either — it splits 3 `noun`
  / 8 `verb` / 1 `prep` across the paradigm, cutting straight through the set
  we want to keep.

The trigger is deliberately **case-blind**: it locates the pair and nothing
more. Whether that pair is عرنجي (Case 1) or temporal (Case 2) is decided by
the مضاف إليه test in V5T-7/V5T-8, and several tests below pin that separation
so a later task cannot quietly fold the decision back in here.

No test in this file reads anything from `doc/` — the sentences are inline, so
it runs on a bare checkout.
"""
import pytest

from app.config import rules_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_qabl_trigger
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

SPEC = reader(rules_path)["qabl"]
PREP_LEX = SPEC["trigger_prep_lex"]
HEAD_SURFACE = SPEC["trigger_head_surface"]


""" unit tests — plain dicts, no CAMeL """


def build(*words):
    """words are (surface, pos, lex) triples -> (tokens, disambiguated)."""
    tokens = [(i, word) for i, (word, _, _) in enumerate(words)]
    disambiguated = [
        {"lex": lex, "pos": pos, "pattern": "", "prc0": "0", "prc1": "0", "prc2": "0"}
        for _, pos, lex in words
    ]
    return tokens, disambiguated


def fires(index, *words):
    tokens, disambiguated = build(*words)
    return is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD_SURFACE)


MIN = ("من", "prep", "من")
QABL = ("قبل", "noun", "قبل")


def test_matches_the_preposition_followed_by_the_head():
    assert fires(0, MIN, QABL) is True


def test_the_match_is_anchored_on_the_preposition():
    """Index 0 is the pair; index 1 is not a second match. A finder that walked
    every token would otherwise report «من قبل» twice."""
    assert fires(0, MIN, QABL) is True
    assert fires(1, MIN, QABL) is False


def test_rejects_the_head_without_the_preposition():
    """«قبل الاجتماع» is an ordinary temporal preposition — not this rule."""
    assert fires(0, QABL, ("الاجتماع", "noun", "اجتماع")) is False


def test_rejects_the_preposition_without_the_head():
    assert fires(0, MIN, ("الوزارة", "noun", "وزارة")) is False


def test_rejects_a_gap_between_the_two():
    """The pair is adjacent by construction. No skip window, unlike v1's
    `next_target_index` or v4's `qam_complement_index`."""
    assert fires(0, MIN, (",", "punc", ","), QABL) is False


def test_does_not_run_off_the_end():
    """«... جاءت من.» — من as the final token must not index past the list."""
    assert fires(0, MIN) is False


def test_rejects_the_preposition_when_it_is_not_tagged_prep():
    """The `pos` guard is cheap and it costs nothing, so it stays — but see
    `test_pos_does_not_separate_the_relative_pronoun` for what it does not buy.
    """
    assert fires(0, ("من", "pron_rel", "من"), QABL) is False


def test_rejects_another_preposition():
    assert fires(0, ("عن", "prep", "عن"), QABL) is False


""" the head is matched on surface — these pin why """


@pytest.mark.parametrize("surface", ["قبلة", "قبلت", "قبلوا", "قبلية", "قبلان"])
def test_rejects_a_word_that_merely_starts_with_the_head(surface):
    """A naive `startswith` would take all of these. Measured in the 1M Leipzig
    news corpus, «من» + a token starting with قبل is 3447 occurrences, of which
    قبلة (×2) and a run-together قبلوفي are not this construction at all."""
    assert fires(0, MIN, (surface, "verb", "قبل")) is False


def test_the_lemma_is_useless_as_the_head_test():
    """All of these arrive with `lex == "قبل"` on the pipeline's own path. If
    the head were matched on lemma, every one would fire."""
    for surface in ["قبلة", "قبلت", "قبلوا"]:
        assert fires(0, MIN, (surface, "verb", "قبل")) is False


@pytest.mark.parametrize("pos", ["noun", "verb", "prep", "adj", ""])
def test_the_head_pos_is_not_consulted(pos):
    """CAMeL reads the head as `noun`, `verb` or `prep` depending on which
    person is attached. Nothing in this rule may depend on which."""
    assert fires(0, MIN, ("قبل", pos, "قبل")) is True


""" real CAMeL — the tagging facts this rule stands on """


def real_fires(sentence):
    """Index of the من that opens a «من قبل» pair, or None."""
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD_SURFACE):
            return index
    return None


@pytest.mark.parametrize(
    "sentence",
    [
        "تمت مراجعة الملف من قبل المشرف",
        "التعليمات الصحية التي تصدر من قبل وزارة الصحة",
        "الإجراءات المتخذة من قبل الحكومة كانت سريعة",
    ],
)
def test_real_fires_on_an_agent_phrase(sentence):
    assert real_fires(sentence) is not None


@pytest.mark.parametrize(
    "sentence",
    [
        "لم يعمل من قبل في مضاعفة توليد الكهرباء",
        "كان قد زار المدينة من قبل",
    ],
)
def test_real_fires_on_a_temporal_phrase_too(sentence):
    """CASE-BLIND, deliberately. Case 2 is فصيح, but it is the *same two
    tokens*; silencing it is V5T-7/V5T-8's job, decided on what follows قبل.
    Deciding it here would put two questions in one function."""
    assert real_fires(sentence) is not None


@pytest.mark.parametrize(
    "sentence",
    [
        "عقد الاجتماع قبل الظهر",
        "وصلت الرسالة من الوزارة أمس",
        "اقترب من قبلة المسجد",
    ],
)
def test_real_stays_silent_without_the_pair(sentence):
    assert real_fires(sentence) is None


def test_real_the_two_tokens_never_merge():
    """The task's own precondition. من is a standalone word, never a proclitic,
    so `simple_word_tokenize` always leaves the pair as two tokens — confirmed
    over all 3447 corpus occurrences, every one of which has من on its own."""
    tokens = preprocess("تمت مراجعة الملف من قبل المشرف")
    surfaces = [word for _, word in tokens]
    assert "من" in surfaces
    assert "قبل" in surfaces
    assert surfaces.index("قبل") == surfaces.index("من") + 1


def test_real_the_head_lemma_collapses_under_dediacritization():
    """The measured fact behind `_is_qabl_head`. CAMeL's vocalized lexes are
    distinct (قِبَل / قَبْلَ / قَبِلَ) but `get_pos_and_pattern_in_context`
    dediacritizes, so they arrive identical."""
    readings = {}
    for surface in ["قبل", "قبله", "قبلنا", "قبلي"]:
        tokens = preprocess(f"صدر القرار من {surface} وانتهى الأمر")
        disambiguated = get_pos_and_pattern_in_context(tokens)
        index = [i for i, word in tokens if word == surface][0]
        readings[surface] = (disambiguated[index]["pos"], disambiguated[index]["lex"])

    assert {lex for _, lex in readings.values()} == {"قبل"}, readings
    assert len({pos for pos, _ in readings.values()}) > 1, readings


""" recorded limitations — no fix in this task, and possibly none at all """


def test_real_pos_does_not_separate_the_relative_pronoun():
    """🔴 «مَن قَبِلَ الهديةَ» ("whoever accepted the gift") is spelled exactly
    like «من قِبَلِ ...» once dediacritized, and CAMeL tags that من as `prep`
    all the same — so the `pos` guard does not exclude it and the pair fires.

    Not fixable downstream either: the مضاف إليه test in V5T-7 sees a noun
    after قبل in both readings. Recorded rather than patched — no example
    appeared in the 64 gold rows, where all 41 explicit-noun rows are Case 1,
    so this is a rare reading in news prose. If it turns up in real text it is
    a false flag, which is the direction the invariant tolerates.
    """
    assert real_fires("من قبل الهدية شكر صاحبها") is not None


@pytest.mark.parametrize("surface", ["قبله", "قبلها", "قبلهم", "قبلنا", "قبلي"])
def test_the_attached_pronoun_forms_are_matched_too(surface):
    """V5T-6 widened `_is_qabl_head` from the bare surface to the full
    attached-pronoun paradigm. The paradigm itself is exercised in
    `test_qabl_clitics.py`; this only pins that the widening reached the
    trigger, since `is_qabl_trigger` is the caller.
    """
    assert fires(0, MIN, (surface, "verb", "قبل")) is True
