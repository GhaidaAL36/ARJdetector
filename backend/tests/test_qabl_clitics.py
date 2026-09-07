# -*- coding: utf-8 -*-
"""V5T-6 — «من قبل» carrying an attached pronoun.

CAMeL cannot be asked which forms these are. Probed over all twelve persons in
context, `lex` is `قبل` for **every one of them** — the vocalized lexes differ
(قِبَل / قَبْلَ / قَبِلَ) but `get_pos_and_pattern_in_context` dediacritizes, so on
the pipeline's own path they arrive identical, and so does قبلة. `pos` splits
the paradigm three ways, cutting through the middle of it:

    قبل، قبله، قبلها                                    -> noun
    قبلهما، قبلهم، قبلهن، قبلك، قبلكما، قبلكم، قبلكن، قبلنا -> verb  («accepted»)
    قبلي                                                -> prep

So the head is matched on **surface**, against Arabic's attached-pronoun
paradigm. That is a closed set fixed by the grammar, not a lexicon that grows
with observation — the distinction this project draws between a mechanism and
an override list. It lives in `rule.py` beside its only consumer, by the same
rule that keeps `VIII_INFIX_BY_RADICAL` in `morphology.py`.

Everything asserted here about real Arabic frequencies was measured by walking
the Leipzig `ara_news_2020_1M` / `_300K` corpora; the counts are in the
docstrings so a later reader can re-derive rather than trust them. **No test in
this file reads `doc/` or the corpus** — the sentences are inline, so it runs on
a bare checkout.
"""
import pytest

from app.config import rules_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import (
    _carries_pronoun,
    _is_qabl_head,
    has_qabl_genitive,
    is_qabl_trigger,
)
from app.engine.tags import PRONOUN_SUFFIXES
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

import goldsets

SPEC = reader(rules_path)["qabl"]
PREP_LEX = SPEC["trigger_prep_lex"]
HEAD = SPEC["trigger_head_surface"]

#: Every person, spelled out rather than generated from the constant under test.
ALL_PERSONS = [
    "قبله", "قبلها", "قبلهما", "قبلهم", "قبلهن",
    "قبلك", "قبلكما", "قبلكم", "قبلكن",
    "قبلي", "قبلنا",
]


""" the paradigm is closed — this is a mechanism, not an override list """


def test_the_paradigm_is_exactly_arabics_pronoun_suffixes():
    """Eleven suffixes: five 3rd person, four 2nd, two 1st. The number is not a
    cap someone chose — it is how many attached pronouns Arabic has. If this
    ever needs an entry added, the entry is not a pronoun and the mechanism is
    wrong."""
    assert PRONOUN_SUFFIXES == {
        "ه", "ها", "هما", "هم", "هن",
        "ك", "كما", "كم", "كن",
        "ي", "نا",
    }
    assert len(PRONOUN_SUFFIXES) == 11


def test_the_paradigm_is_immutable():
    """A frozenset, so no caller can widen it at runtime."""
    assert isinstance(PRONOUN_SUFFIXES, frozenset)


def test_the_duals_are_present():
    """`هما` and `كما` were missing from the paradigm as first recorded, and the
    omission was real: «من قبلهما» occurs 6 times in the 1M corpus. Found by
    walking the corpus, not by writing the paradigm out from memory — which is
    why this line exists rather than a comment."""
    assert "هما" in PRONOUN_SUFFIXES
    assert "كما" in PRONOUN_SUFFIXES


def test_the_bare_form_still_works_with_the_paradigm_empty():
    """Degradation check, same discipline as v2's and v4's override lists: with
    the list empty the tool still behaves correctly, losing only the forms the
    list recovers."""
    assert _is_qabl_head("قبل", HEAD, pronoun_suffixes=frozenset()) is True
    assert _is_qabl_head("قبلنا", HEAD, pronoun_suffixes=frozenset()) is False


""" every person is accepted """


@pytest.mark.parametrize("surface", ALL_PERSONS)
def test_accepts_every_person(surface):
    assert _is_qabl_head(surface, HEAD) is True


def test_accepts_the_bare_form():
    assert _is_qabl_head(HEAD, HEAD) is True


""" the near misses are rejected — an exact test, not a prefix test """


@pytest.mark.parametrize(
    "surface",
    [
        "قبلة",      # kiss / qibla — appears twice after من in the 300K corpus
        "قبلت",      # she/I accepted
        "قبلتها",
        "قبلته",
        "قبلوا",
        "قبلناها",   # the verb with BOTH a subject and an object suffix
        "قبلية",     # tribal
        "قبليون",
        "قبلان",
        "قبلاوي",
        "قبلوفي",    # a run-together «من قبل وفي» — real, once in the corpus
    ],
)
def test_rejects_a_word_that_merely_starts_with_the_head(surface):
    """`startswith` alone would take all of these. The remainder has to be an
    actual pronoun suffix, which costs nothing and removes them."""
    assert _is_qabl_head(surface, HEAD) is False


def test_rejects_an_invisible_character_after_the_head():
    """Real corpus data: one occurrence is قبل followed by U+202E
    (RIGHT-TO-LEFT OVERRIDE). It is not the bare form and its remainder is not a
    pronoun, so it is rejected — worth pinning because a prefix test would take
    it and a `strip()` somewhere upstream would hide it."""
    assert _is_qabl_head("قبل‮", HEAD) is False


def test_rejects_a_word_that_does_not_start_with_the_head():
    assert _is_qabl_head("مقبلة", HEAD) is False
    assert _is_qabl_head("استقبل", HEAD) is False


""" real CAMeL — the trigger reaches these despite the tagging """


def real_fires(sentence):
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD):
            return index
    return None


@pytest.mark.parametrize(
    "sentence",
    [
        "تحظى بتقدير واحترام من قبلنا",
        "فليكن الأسلوب من قبلهم وقبلنا",
        "كما كان الحال مع إيبوي من قبله",
        "الرسالة موقعة من قبلك",
        "صنف من قبلها كداعم للإرهاب",
    ],
)
def test_real_fires_on_a_clitic_form(sentence):
    """Four of these five have the head tagged `verb`/`قبل` — the reading that
    made a lemma test impossible. The surface match reaches them anyway."""
    assert real_fires(sentence) is not None


def test_real_the_paradigm_is_tagged_three_different_ways():
    """The measurement the surface match exists for. Not a fixed expectation of
    which person gets which tag — that is CAMeL's business and may move — but a
    pin on the thing that matters: `pos` is not constant across the paradigm,
    and `lex` is constant across all of it, so neither can be the test."""
    poses, lexes = set(), set()
    for surface in ["قبل"] + ALL_PERSONS:
        tokens = preprocess(f"صدر القرار من {surface} وانتهى الأمر")
        disambiguated = get_pos_and_pattern_in_context(tokens)
        index = [i for i, word in tokens if word == surface][0]
        poses.add(disambiguated[index]["pos"])
        lexes.add(disambiguated[index]["lex"])

    assert lexes == {"قبل"}, lexes
    assert len(poses) >= 3, poses


def test_real_every_person_is_a_single_token():
    """`simple_word_tokenize` never splits the pronoun off, so the surface the
    trigger compares is the whole form. Checked for all eleven — a split would
    make the paradigm unreachable without any test failing elsewhere."""
    for surface in ALL_PERSONS:
        tokens = preprocess(f"صدر القرار من {surface} وانتهى الأمر")
        assert surface in [word for _, word in tokens], surface


def test_real_stays_silent_on_a_near_miss_in_context():
    assert real_fires("اقترب من قبلة المسجد") is None
    assert real_fires("عاد من قبلية بعيدة") is None


""" recorded limitation — the clitic zone """


def test_real_fires_on_the_case_three_sentences_it_cannot_decide():
    """🔴 KNOWN. «من قبلنا» meaning *from our side* (Case 3, فصيح) and «من
    قبلنا» meaning *by us* (Case 1, عرنجي) are the same eleven characters, and
    the sentences are structurally identical — the مضاف إليه test in V5T-7
    cannot separate them either. All three errors on the 64-row gold set live
    here.

    Sized before being patched: pronoun clitics are 53 of 3,395 real
    occurrences (~1.6%), ~30% wrong, so ~0.5% overall — entirely false flags.
    Abstaining on clitics would trade those 3 for 7 missed عرنجية, which the
    zero-missed-عرنجية invariant forbids. So the trigger fires and the error is
    accepted. V5T-18 is where that decision gets revisited with more data.
    """
    assert real_fires("تحظى بتقدير واحترام من قبلنا") is not None


""" the clitic gold set — what flagging every clitic actually costs

NOTE: reads doc/v5_clitics.csv, which is gitignored — Ghaida's own labelled
sentences (193 rows, every «من قبل + ضمير» in the Leipzig 1M corpus, labelled
2026-09-02). Routed through `tests/goldsets.py`, so a checkout without the file
SKIPS this section instead of failing.
"""

CLITIC_GOLD = "v5_clitics.csv"


def _case(row):
    """Her labels are Arabic: حكمك is عرنجي/فصيح, case is الاولى/الثانية/الثالثة.

    Row n=3 has the two columns transposed at source; both orderings are read
    so the set scores correctly either way. When that row is fixed this becomes
    a no-op — it is not a general tolerance for bad labels.
    """
    verdict, case = row["حكمك"].strip(), row["case"].strip()
    if verdict not in ("عرنجي", "فصيح"):
        verdict, case = case, verdict
    return verdict == "عرنجي", {"الاولى": 1, "الأولى": 1, "الثانية": 2, "الثالثة": 3}[case]


@goldsets.needs(CLITIC_GOLD)
def test_flagging_every_clitic_costs_what_the_record_says():
    """🔴 THE LIMITATION, MEASURED — 193 rows, not the 10 it used to rest on.

    The clitic branch has no decision to make: a pronoun is a مضاف إليه, so
    every one of these flags. Against Ghaida's labels that is 145 right and 48
    wrong, and **every error is a false flag** — the tolerated direction.

        Case 1  عرنجي  145   flagged correctly
        Case 2  فصيح    25   temporal «من قبله» — "before him"
        Case 3  فصيح    23   الجهة — «تحظى بتقدير واحترام من قبلنا»

    Clitics are ~1.65% of real «من قبل», so this is ~0.41% error overall.
    """
    rows = goldsets.rows(CLITIC_GOLD)
    assert len(rows) == 193

    by_case = {1: 0, 2: 0, 3: 0}
    correct = missed = false_flags = 0
    for row in rows:
        should_flag, case = _case(row)
        by_case[case] += 1

        # Score the occurrence the row is ABOUT. Two sentences here (n=69, 70)
        # carry both a bare «من قبل» and a clitic one — «ورد الليكود من قبل على
        # تقارير … ممن شغلوا المنصب من قبله» — and the sampler selected them for
        # the clitic, so that is the one Ghaida labelled. Taking the first
        # trigger instead scores the wrong half of the sentence.
        tokens = preprocess(row["sentence"])
        disambiguated = get_pos_and_pattern_in_context(tokens)
        verdict = None
        for index, _ in tokens:
            if not is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD):
                continue
            if _carries_pronoun(tokens[index + 1][1], HEAD):
                verdict = has_qabl_genitive(tokens, index + 1, disambiguated, HEAD)
                break

        assert verdict is not None, f"no clitic occurrence found: {row['sentence']}"
        if verdict == should_flag:
            correct += 1
        elif should_flag:
            missed += 1
        else:
            false_flags += 1

    assert by_case == {1: 145, 2: 25, 3: 23}, by_case
    assert missed == 0, f"{missed} missed عرنجية — the invariant this rule may not break"
    assert (correct, false_flags) == (145, 48), (correct, false_flags)


@goldsets.needs(CLITIC_GOLD)
def test_the_trigger_finds_every_row():
    """The 193 were pulled by a standalone script; this proves the *runtime*
    trigger reaches all of them too, so the two paths cannot drift."""
    for row in goldsets.rows(CLITIC_GOLD):
        tokens = preprocess(row["sentence"])
        disambiguated = get_pos_and_pattern_in_context(tokens)
        assert any(
            is_qabl_trigger(tokens, i, disambiguated, PREP_LEX, HEAD)
            for i, _ in tokens
        ), row["sentence"]


""" V5T-18 — the decision, and the counterfactual that settles it """


@goldsets.needs(CLITIC_GOLD)
def test_abstaining_on_clitics_would_break_the_invariant():
    """V5T-18 asked: flag the pronoun cases, or abstain on them?

    The task was blocked pending "the held-out numbers and the wider Case 3
    sample". Both exist now, and they make the answer more decisive than the
    10-row estimate it was parked on — the original framing was 3 false flags
    against 7 missed; on 193 rows it is 48 against 145.

    This test asserts the counterfactual rather than leaving it in prose, so
    anyone proposing the switch has to delete a failing test that states its
    cost. Abstaining is not a tuning choice; it converts every Case 1 clitic
    into a silent miss, which is the one error this rule may not make.
    """
    rows = goldsets.rows(CLITIC_GOLD)
    would_be_missed = [row for row in rows if _case(row)[0] is True]
    would_be_saved = [row for row in rows if _case(row)[0] is False]

    assert len(would_be_missed) == 145
    assert len(would_be_saved) == 48
    ratio = len(would_be_missed) / len(would_be_saved)
    assert ratio > 3.0, f"three missed عرنجية bought per false flag saved: {ratio:.1f}"


@goldsets.needs(CLITIC_GOLD)
def test_the_clitic_branch_still_flags_unconditionally():
    """The decision itself, pinned. A pronoun IS a مضاف إليه, so the branch has
    nothing to decide — and V5T-18 confirms it should stay that way. If this
    ever fails, someone has added a suppression path and owes the measurement.
    """
    for row in goldsets.rows(CLITIC_GOLD)[:40]:
        tokens = preprocess(row["sentence"])
        disambiguated = get_pos_and_pattern_in_context(tokens)
        for index, _ in tokens:
            if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD) and \
                    _carries_pronoun(tokens[index + 1][1], HEAD):
                assert has_qabl_genitive(tokens, index + 1, disambiguated, HEAD) is True
                break
