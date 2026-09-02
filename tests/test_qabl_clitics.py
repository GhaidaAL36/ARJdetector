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
from app.engine.rule import _is_qabl_head, is_qabl_trigger
from app.engine.tags import PRONOUN_SUFFIXES
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

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
