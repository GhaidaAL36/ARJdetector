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

import goldsets

from app.config import rules_path, whitelist_path
from app.engine.rule import is_result_noun
from app.engine.rule_engine import analyze
from app.rules.rule_loader import reader

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


@goldsets.needs("labelled_set.csv")
def test_real_labelled_set_is_fully_correct():
    rows = [r for r in goldsets.rows("labelled_set.csv")
            if r.get("gold") in ("FLAG", "SILENT", "NO-TRIGGER")]
    wrong = [(r["gold"], r["sentence"]) for r in rows
             if qam_flags(r["sentence"]) != (r["gold"] == "FLAG")]

    assert wrong == []
    assert len(rows) == 31


def test_real_context_grid_has_zero_missed_arnajiyya():
    """THE STANDING INVARIANT. A false flag is visible and arguable; a missed
    flag is invisible and the writer never learns the tool had nothing to say."""
    missed = []
    for r in goldsets.rows("context_test.csv"):
        if not r.get("الجملة"):
            continue
        if r["حكمك"].strip() == "عرنجي" and not qam_flags(r["الجملة"]):
            missed.append(r["الجملة"])

    assert missed == []


def test_real_context_grid_has_no_false_flags():
    """The جولة false flag is gone: «بجولة مفاوضات» is a licensed pair."""
    false_flags = [r["الجملة"]
                   for r in goldsets.rows("context_test.csv")
                   if r.get("الجملة") and r["حكمك"].strip() == "فصيح"
                   and qam_flags(r["الجملة"])]

    assert false_flags == []


""" the list is closed, and cannot silence a real flag """


def test_the_result_noun_list_matches_the_closed_categories():
    """قاعدة §2.2 — five closed categories of nouns that take no derived verb
    carrying the same meaning. Stored as lemmas: أمانة/عهدة/أعباء lemmatise to
    أمان/عهد/عبء, so the surfaces would never match."""
    assert set(RESULT_NOUNS) == {
        "دور", "وظيفة", "مهمة", "رسالة", "مقام",
        "واجب", "حق", "التزام", "مسؤولية", "أمان", "عهد",
        "أمر", "شأن", "عبء",
    }


def test_section_2_2_outranks_section_1_3():
    """A described مصدر with NO derived verb stays فصيح — «قام المدير
    بمسؤولياته كاملة» has nothing to collapse to, so the الصفة is irrelevant.
    Order matters: §1.3 assumes a collapse exists."""
    assert qam_flags("قام المدير بمسؤولياته كاملة") is False
    assert qam_flags("قام الوصي بأمر اليتيم") is False


@pytest.mark.parametrize(
    "sentence", ["قامت الحكومة بإصلاح شامل", "قام الطبيب بفحص دقيق",
                 "قام الفريق بمحاولة أخيرة", "قام المركز بمسح ميداني"]
)
def test_real_a_described_masdar_flags(sentence):
    """§1.3 (2026-08-28) — الصفة does not protect the sentence; it collapses to
    a مفعول مطلق موصوف: «أصلحت الحكومة إصلاحًا شاملًا». Case 5 is withdrawn."""
    assert qam_flags(sentence) is True


@pytest.mark.parametrize(
    "sentence", ["قام الموظف بدوره في المشروع", "قام القائد بواجب الدفاع عن المدينة",
                 "قام المدير بمسؤولياته", "قام الوصي بأمر اليتيم"]
)
def test_real_each_listed_noun_earns_its_entry(sentence):
    assert qam_flags(sentence) is False


""" negation does NOT suppress — Case 2 was withdrawn 2026-08-28 """


@pytest.mark.parametrize(
    "sentence",
    [
        "لم يقم المسؤول بأي إجراء",
        "لن تقوم بأي محاولة",
        "ما قامت بأي مراجعة",
        "لم تقم اللجنة بأية خطوة",
        "لم يقم الباحث بدراسة الظاهرة",
    ],
)
def test_real_negation_flags(sentence):
    """Ghaida's ruling: «لم يقم بأي إجراء» → «لم يتخذ أي إجراء» holds, so the
    periphrasis is redundant and this is عرنجي. القاعدة row 2 called it فصيح;
    that row is withdrawn."""
    assert qam_flags(sentence) is True


def test_real_a_quantifier_does_not_hide_the_real_head():
    """أي takes the بـ, so «لم يقم بأي عملية إنقاذ» has عملية — a listed result
    noun — one token past the complement. Without complement_head_index this
    would test أي against the list and wrongly flag."""
    assert qam_flags("لم يقم بأي دور في المشروع") is False
    assert qam_flags("لم يقم بأي واجب") is False


""" the two-step decision order — قاعدة §3, 2026-08-28 """


def test_the_verification_step_runs_after_the_collapse_step():
    """ORDER IS LOAD-BEARING, and this asserts it rather than the outcome.

    §3.1 collapse step: does the sentence take a direct verb / مفعول مطلق?
    §3.2 verification: only if the collapse BREAKS — series, or a نهوض/تكفّل noun.

    «قام المدير بمسؤولياته كاملة» is the case that separates the two orders. It
    is a described مصدر, so §1.3 alone would flag it; but مسؤولية has no derived
    verb, so the collapse never holds and the verification step silences it.
    Run the steps the other way round and this becomes a missed... no — a WRONG
    FLAG on فصيح Arabic.
    """
    assert qam_flags("قام المدير بمسؤولياته كاملة") is False
    assert qam_flags("قام الطبيب بفحص دقيق") is True


def test_a_series_is_checked_before_the_noun_list():
    """Both are §3.2 verification checks, and a sentence can satisfy either.
    «قام بالقراءة والتصحيح» is a series whose members are NOT listed nouns —
    only the series check can silence it."""
    assert qam_flags("قام بالقراءة والتصحيح") is False


@pytest.mark.parametrize(
    "sentence",
    ["قام بدوره", "قام بواجبه", "قام الوصي بأمر اليتيم", "قام الأب بشأن أسرته",
     "قام الموظف بوظيفته", "قام المعلم برسالته"],
)
def test_real_the_verification_list_covers_qaida_categories(sentence):
    """§2.2's five closed categories — الوظائف، التكاليف، النهوض، الأحداث
    الكبرى، الفرق التشغيلية."""
    assert qam_flags(sentence) is False


""" pair-keyed licensing — جولة, قاعدة 2026-08-28 """

LICENSED = reader(whitelist_path)["qam"]["licensed_pairs"]


@pytest.mark.parametrize(
    "sentence",
    ["قام الطرفان بجولة مفاوضات", "قام الوفدان بجولة محادثات",
     "قامت اللجنة بجولة تفتيش", "قام الفريق بجولة استطلاع",
     "قام الوفد بجولة حوار", "قام الوفد بجولة تراخيص"],
)
def test_real_a_licensed_pair_is_silent(sentence):
    """جولة + a procedural stage is a *round* of something — قام بـ carries
    that meaning and there is no single verb for it."""
    assert qam_flags(sentence) is False


@pytest.mark.parametrize(
    "sentence",
    ["قام الوفد بجولة في المدينة", "قام الزائر بجولة في المتحف",
     "قام الوفد بجولة تفقدية", "قامت اللجنة بجولة ميدانية",
     "قام الفريق بجولة استكشافية", "قام بجولة واسعة"],
)
def test_real_an_unlicensed_جولة_flags(sentence):
    """Place or adjective — «جال/تجوّل في المدينة»، «تفقّد». These need no
    blacklist: they flag by default, which is why القاعدة's blacklist is
    deliberately not encoded."""
    assert qam_flags(sentence) is True


def test_the_licensing_words_are_stored_as_lemmas():
    """مفاوضات/محادثات/تراخيص lemmatise to the singular; surface entries would
    silently never match."""
    assert set(LICENSED["جولة"]) == {
        "مفاوضة", "محادثة", "استطلاع", "ترخيص", "تفتيش", "حوار", "استكشاف"
    }


def test_only_one_word_needs_pair_keying():
    """A probe, not a mechanism. If a second word needs this, build the general
    (مصدر + complement head) table CLAUDE.md predicted; while جولة stands alone
    it is a bounded exception."""
    assert list(LICENSED) == ["جولة"]


def test_the_rule_works_with_the_pair_list_empty():
    from app.engine.rule import is_licensed_pair

    assert is_licensed_pair([{"lex": "جولة"}, {"lex": "مفاوضة"}], 0, {}) is False


""" §2.1 duty nouns — a KNOWN-INCOMPLETE list, grows only from observed text """

DUTY = reader(whitelist_path)["qam"]["duty_nouns"]


@pytest.mark.parametrize(
    "sentence",
    ["قام القاضي بالعدل بين الخصوم", "قام الأب برعاية أبنائه",
     "قام الحارس بحراسة المرمى"],
)
def test_real_duty_nouns_are_silent(sentence):
    """Found by Ghaida's 70-sentence manual run, 2026-08-28 — the only three
    false positives in that set. قام بـ here means النهوض بالمسؤولية."""
    assert qam_flags(sentence) is False


def test_duty_nouns_are_separate_from_result_nouns():
    """Different criteria, so different lists. result_nouns = no derived verb;
    duty_nouns all HAVE verbs (عَدَلَ، رَعَى، حَرَسَ) and are فصيح for the
    sense. Merging them would quietly turn a bounded list into an open one."""
    assert set(DUTY).isdisjoint(set(RESULT_NOUNS))


def test_no_duty_noun_would_silence_a_real_flag():
    """Same safety property as result_nouns: nothing on this list may appear as
    the complement of a gold FLAG row."""
    import csv as _csv
    import io as _io

    from app.engine.analysis import get_pos_and_pattern_in_context
    from app.engine.rule import complement_head_index, is_qam_trigger
    from app.engine.rule_engine import qam_complement_index
    from app.text.preprocessor import preprocess

    spec, over = reader(rules_path)["qam"], reader(whitelist_path)["qam"]
    flagged = set()
    for row in goldsets.rows("labelled_set.csv"):
            if row.get("gold") != "FLAG":
                continue
            tokens = preprocess(row["sentence"])
            entries = get_pos_and_pattern_in_context(tokens)
            for index, _ in tokens:
                if is_qam_trigger(tokens, index, entries, spec["trigger_lex"],
                                  over["mistagged_surfaces"]):
                    c = qam_complement_index(tokens, index, entries)
                    h = complement_head_index(entries, c)
                    if h is not None:
                        flagged.add(entries[h]["lex"])
                    break

    assert sorted(set(DUTY) & flagged) == []


def test_the_duty_list_stays_small_and_observed():
    """It cannot be completed — whether a مصدر denotes a duty is meaning, and
    the sentence is structurally identical to an عرنجي one. Entries come from
    real sentences seen flagged wrongly, never from enumerating the language.
    If this grows past a handful, that is a finding about the mechanism."""
    assert len(DUTY) <= 15


def test_the_rule_works_with_the_duty_list_empty():
    from app.engine.rule import is_duty_noun

    assert is_duty_noun([{"lex": "رعاية"}], 0, []) is False
