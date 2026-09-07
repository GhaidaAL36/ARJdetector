# -*- coding: utf-8 -*-
"""V5T-7 and V5T-8 — the مضاف إليه test, which is the whole v5 decision.

    does قبل have a مضاف إليه?
      no   ->  SILENT   (Case 2, ظرفية زمانية — «زار المدينة من قبل»)
      yes  ->  FLAG     (Case 1, فاعل لمبنيّ للمجهول — «رُوجع من قبل المشرف»)

Two ways to have one, and the first is why V5T-6 came before this task: **an
attached pronoun IS the مضاف إليه**, so «من قبله» has one no matter what
follows. Otherwise it is the next token, judged on `pos`.

**`stt` cannot be used**, and this is measured: CAMeL reports `stt=c`
(construct) on قبل unconditionally — including bare, sentence-final «…من قبل.»
with no genitive anywhere in the sentence. Another field that does not mean
what its name says. The next token is checked directly.

**The `pos` test is a DENY-list, and the polarity is the safety property.**
`NON_GENITIVE_POS` names the function-word tags that cannot head a مضاف إليه;
everything else counts as one. An allow-list would default to *silence*, and a
silent miss is the one error this rule may not make.

That choice could not have been made on `doc/v5_review_sample.csv` — measured,
an allow-list of `{noun, noun_prop, adj}` and this deny-list **both score 61/64
there**, because the 64 rows contain none of the deciding cases. It was decided
on 1,469 bare «من قبل» occurrences drawn from the Leipzig 300K corpus, where
the two designs differ on 30 sentences:

    26 real agents   من قبل 3 شبان · من قبل هذه الميليشيات · من قبل أي دولة
                     من قبل الذين يفهمون · من قبل فيلق القدس · من قبل أحد الأهالي
     4 temporal      وحاول أرسنال من قبل ضم ليمار · سمعت ذلك من قبل تسبب…

The allow-list turns those 26 into missed عرنجية (1.8% of real occurrences, the
forbidden direction); the deny-list turns the 4 into false flags (0.27%,
tolerated). CAMeL mistags several of the 26 — `أغلب` and `فيلق` and `حوت` come
back `verb`, `أحد` comes back `foreign` — which is itself the argument against
enumerating the tags that may pass.

This is the caveat in CLAUDE.md biting in practice: the 64 rows were used to
*choose* the mechanism, so they cannot measure it.
"""
import pytest

from app.config import rules_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import has_qabl_genitive, is_qabl_trigger
from app.engine.tags import NON_GENITIVE_POS
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

import goldsets

SPEC = reader(rules_path)["qabl"]
PREP_LEX = SPEC["trigger_prep_lex"]
HEAD = SPEC["trigger_head_surface"]


def build(*words):
    tokens = [(i, word) for i, (word, _) in enumerate(words)]
    disambiguated = [
        {"lex": "", "pos": pos, "pattern": "", "prc0": "0", "prc1": "0", "prc2": "0"}
        for _, pos in words
    ]
    return tokens, disambiguated


def has_genitive(head_index, *words):
    tokens, disambiguated = build(*words)
    return has_qabl_genitive(tokens, head_index, disambiguated, HEAD)


""" V5T-7 — an attached pronoun is itself the مضاف إليه """


@pytest.mark.parametrize(
    "surface", ["قبله", "قبلها", "قبلهما", "قبلهم", "قبلك", "قبلي", "قبلنا"]
)
def test_a_pronoun_counts_whatever_follows(surface):
    """Checked against a following token that would otherwise silence it, so
    the test proves the clitic branch short-circuits rather than agreeing with
    the next-token branch by accident."""
    assert has_genitive(0, (surface, "noun"), (".", "punc")) is True


def test_the_pronoun_branch_needs_no_next_token_at_all():
    """«…من قبله.» ends the sentence and still has its مضاف إليه."""
    assert has_genitive(0, ("قبله", "noun")) is True


""" V5T-7 — otherwise it is the next token """


@pytest.mark.parametrize(
    "pos", ["noun", "noun_prop", "adj", "pron_dem", "pron_rel", "digit", "foreign"]
)
def test_a_nominal_next_token_is_a_genitive(pos):
    assert has_genitive(0, ("قبل", "noun"), ("س", pos)) is True


def test_an_unfamiliar_tag_counts_as_a_genitive():
    """The deny-list's whole point. A tag nobody enumerated must FLAG, not
    silence — CAMeL invents tags this project has not seen, and every one of
    them arriving as a silent miss is the failure mode the invariant forbids."""
    assert has_genitive(0, ("قبل", "noun"), ("س", "some_new_camel_tag")) is True
    assert has_genitive(0, ("قبل", "noun"), ("س", "")) is True


""" V5T-8 — Case 2, the silent branch """


@pytest.mark.parametrize("pos", sorted(NON_GENITIVE_POS))
def test_a_function_word_is_not_a_genitive(pos):
    assert has_genitive(0, ("قبل", "noun"), ("س", pos)) is False


def test_nothing_after_the_head_is_not_a_genitive():
    """«كان قد زار المدينة من قبل» — the head ends the token list."""
    assert has_genitive(0, ("قبل", "noun")) is False


def test_the_test_is_not_sentence_position():
    """The trap V5T-8 names. «لم يعمل من قبل في مضاعفة…» is temporal *with* a
    word after it; «المحدّدة من قبل فيفا» is an agent. A "is قبل sentence-final"
    test gets both wrong, so the two must part on `pos` alone."""
    assert has_genitive(0, ("قبل", "noun"), ("في", "prep")) is False
    assert has_genitive(0, ("قبل", "noun"), ("فيفا", "noun_prop")) is True


""" real CAMeL, end to end """


def decide(sentence):
    """Trigger, then the مضاف إليه test — the v5 decision as it will be wired."""
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD):
            return has_qabl_genitive(tokens, index + 1, disambiguated, HEAD)
    return None


@pytest.mark.parametrize(
    "sentence",
    [
        "تمت مراجعة الملف من قبل المشرف",
        "التعليمات الصحية التي تصدر من قبل وزارة الصحة",
        "القائمة المحددة من قبل فيفا",
        "قتل الرجل من قبل 3 شبان",
        "تتم الهجمات من قبل هذه الميليشيات",
        "يجب تصنيعها من قبل الذين يفهمون هذه التكنولوجيا",
        "لا يجوز استخدامها من قبل أي دولة",
    ],
)
def test_real_flags_an_agent_phrase(sentence):
    assert decide(sentence) is True


@pytest.mark.parametrize(
    "sentence",
    [
        "كان قد زار المدينة من قبل",
        "لم يعمل من قبل في مضاعفة توليد الكهرباء",
        "لم يحدث هذا من قبل، وهو أمر مفاجئ",
        "تواجد الإسرائيليون هناك من قبل ولكن الوضع تغير",
    ],
)
def test_real_stays_silent_on_a_temporal_phrase(sentence):
    assert decide(sentence) is False


def test_real_stt_is_useless_here():
    """Pinned because it looks like the right field and is not. `stt=c` shows up
    on قبل whether or not a مضاف إليه exists, so a `stt`-based test would flag
    every Case 2 sentence."""
    from app.engine.analysis import _get_mle

    readings = {}
    for sentence in ["تمت المراجعة من قبل المشرف", "كان قد زار المدينة من قبل"]:
        words = [word for _, word in preprocess(sentence)]
        analyses = _get_mle().disambiguate(words)
        index = words.index("قبل")
        readings[sentence] = analyses[index].analyses[0].analysis.get("stt")

    assert len(set(readings.values())) == 1, readings


""" the gold set

NOTE: reads doc/v5_review_sample.csv, which is gitignored — Ghaida's own
labelled sentences. Routed through `tests/goldsets.py`, so a checkout without
the file SKIPS this section instead of failing.
"""

GOLD = "v5_review_sample.csv"


@goldsets.needs(GOLD)
def test_the_gold_set_scores_as_recorded():
    """61/64 with ZERO missed عرنجية — the figure CLAUDE.md records, re-derived
    from the labels rather than trusted. All three errors are false flags on
    «من قبل + ضمير», the documented clitic zone."""
    rows = goldsets.rows(GOLD)
    assert len(rows) == 64

    correct = missed = false_flags = 0
    for row in rows:
        tokens = preprocess(row["sentence"])
        disambiguated = get_pos_and_pattern_in_context(tokens)
        verdict = None
        for index, _ in tokens:
            if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD):
                verdict = has_qabl_genitive(tokens, index + 1, disambiguated, HEAD)
                break
        gold = row["حكمك"] == "FLAG"
        if verdict == gold:
            correct += 1
        elif gold:
            missed += 1
        else:
            false_flags += 1

    assert missed == 0, f"{missed} missed عرنجية — the invariant this rule may not break"
    assert (correct, false_flags) == (61, 3), (correct, false_flags)


@goldsets.needs(GOLD)
def test_every_missed_case_is_a_clitic():
    """The errors are confined to «من قبل + ضمير», which is what makes the
    limitation sizeable (~1.6% of real occurrences) rather than open-ended. If
    a non-clitic error ever appears, the mechanism has a new failure mode."""
    from app.engine.rule import _carries_pronoun

    for row in goldsets.rows(GOLD):
        tokens = preprocess(row["sentence"])
        disambiguated = get_pos_and_pattern_in_context(tokens)
        for index, _ in tokens:
            if is_qabl_trigger(tokens, index, disambiguated, PREP_LEX, HEAD):
                verdict = has_qabl_genitive(tokens, index + 1, disambiguated, HEAD)
                if verdict != (row["حكمك"] == "FLAG"):
                    head = tokens[index + 1][1]
                    assert _carries_pronoun(head, HEAD), row["sentence"]
                break
