# -*- coding: utf-8 -*-
import pytest

from app.config import rules_path, whitelist_path
from app.engine.rule import is_qam_trigger
from app.rules.rule_loader import reader

QAM_TRIGGER_LEXES = reader(rules_path)["qam"]["trigger_lex"]
QAM_MISTAGGED_SURFACES = reader(whitelist_path)["qam"]["mistagged_surfaces"]
from app.text.preprocessor import preprocess
from app.engine.analysis import get_pos_and_pattern_in_context

""" is_qam_trigger — unit tests, no CAMeL """


def build(*words):
    """words are (surface, pos, lex) triples -> (tokens, disambiguated)."""
    tokens = [(i, w) for i, (w, _, _) in enumerate(words)]
    disambiguated = [
        {"lex": lex, "pos": pos, "pattern": "", "prc0": "0", "prc1": "0", "prc2": "0"}
        for _, pos, lex in words
    ]
    return tokens, disambiguated


def fires(index, *words, lexes=QAM_TRIGGER_LEXES, mistagged=QAM_MISTAGGED_SURFACES):
    tokens, disambiguated = build(*words)
    return is_qam_trigger(tokens, index, disambiguated, lexes, mistagged)


def test_matches_the_lemma_as_a_verb():
    assert fires(0, ("قام", "verb", "قام")) is True


def test_rejects_the_lemma_when_it_is_not_a_verb():
    """قوم is a common noun — «ذهب قوم إلى المدينة». pos is what excludes it."""
    assert fires(0, ("قوم", "noun", "قوم")) is False


def test_rejects_another_verb():
    assert fires(0, ("ذهب", "verb", "ذهب")) is False


@pytest.mark.parametrize("lex", ["مقام", "قيام", "إقامة", "قامة", "تقويم"])
def test_rejects_a_noun_that_merely_shares_the_root(lex):
    assert fires(0, (lex, "noun", lex)) is False


def test_matches_nothing_when_the_lex_set_is_empty():
    """With the lex set empty the lemma path is dead — only the mistag
    correction can still fire, and it needs its own surface + negation."""
    assert fires(0, ("قام", "verb", "قام"), lexes=frozenset()) is False


def test_honours_a_caller_supplied_lex_set():
    """The set is a parameter, so data/ can carry it once V4-8 defines the schema."""
    assert fires(0, ("قام", "verb", "قام"), lexes={"قام"}) is True
    assert fires(0, ("قم", "verb", "قم"), lexes={"قام"}) is False


""" the نقم correction — CAMeL tags the 1p jussive as noun/نقمة """


def test_recovers_naqum_after_a_negation_particle():
    assert fires(1, ("لم", "part_neg", "لم"), ("نقم", "noun", "نقمة")) is True


def test_recovers_naqum_after_any_negation_particle():
    """Read from pos, not a hardcoded لم/لا/لن list."""
    assert fires(1, ("لا", "part_neg", "لا"), ("نقم", "noun", "نقمة")) is True


def test_leaves_naqum_alone_without_a_negation_particle():
    """«حلت بهم نقم كثيرة» — the genuine noun, after a preposition."""
    assert fires(2, ("حلت", "verb", "حل"), ("بهم", "prep", "ب"), ("نقم", "noun", "نقمة")) is False


def test_leaves_naqum_alone_at_the_start_of_the_sentence():
    """No preceding token to inspect — must not wrap round to the last one."""
    assert fires(0, ("نقم", "noun", "نقمة"), ("الشعب", "noun", "شعب")) is False


def test_the_correction_does_not_fire_on_other_surfaces():
    """Only نقم is corrected; a negated noun in general is still a noun."""
    assert fires(1, ("لم", "part_neg", "لم"), ("كتاب", "noun", "كتاب")) is False


def test_the_correction_is_absent_by_default():
    """Same shape as v2's force lists — no override unless data supplies one."""
    tokens, disambiguated = build(("لم", "part_neg", "لم"), ("نقم", "noun", "نقمة"))

    assert is_qam_trigger(tokens, 1, disambiguated, QAM_TRIGGER_LEXES) is False


def test_the_trigger_still_works_with_the_correction_list_empty():
    """The tool must behave correctly with the list empty, losing only the one
    form the correction recovers."""
    tokens, disambiguated = build(("قام", "verb", "قام"), ("بدراسة", "noun", "دراسة"))

    assert is_qam_trigger(tokens, 0, disambiguated, QAM_TRIGGER_LEXES, []) is True


""" the data files carry the configuration, not the Python """


def test_trigger_lexes_come_from_rules_json():
    assert set(QAM_TRIGGER_LEXES) == {"قام", "قم", "قوم"}


def test_the_correction_list_stays_bounded():
    """One entry, for one measured CAMeL mistag. If this grows, the mechanism
    is wrong — it is not a place to park unrelated tagging failures."""
    assert set(QAM_MISTAGGED_SURFACES) == {"نقم"}


def test_the_v2_trigger_keys_are_untouched():
    """Adding v4 keys must not disturb what v1 and v2 read."""
    rules = reader(rules_path)

    assert rules["trigger_word"] == "بشكل"
    assert rules["tam_trigger_lex"] == "تم"


""" the conjugation probe, against real CAMeL output """

# (label, sentence, the قام-form the sentence uses)
CONJUGATIONS = [
    ("perfect 3ms", "قام الباحث بدراسة الظاهرة", "قام"),
    ("perfect 3fs", "قامت اللجنة بمراجعة الطلب", "قامت"),
    ("perfect 3md", "قاما بتنفيذ المشروع", "قاما"),
    ("perfect 3fd", "قامتا بتوزيع الأوراق", "قامتا"),
    ("perfect 3mp", "قاموا بتحليل العينات", "قاموا"),
    ("perfect 3fp", "قمن بزيارة المريض", "قمن"),
    ("perfect 2ms", "قمت بمراجعة النص", "قمت"),
    ("perfect 2mp", "قمتم بإصلاح الجهاز", "قمتم"),
    ("perfect 2fp", "قمتن بتوزيع المساعدات", "قمتن"),
    ("perfect 2d", "قمتما بمسح المنطقة", "قمتما"),
    ("perfect 1p", "قمنا بدراسة الحالة", "قمنا"),
    ("imperf 3ms", "يقوم الفريق بمسح المنطقة", "يقوم"),
    ("imperf 3fs", "تقوم الوزارة بتنفيذ الخطة", "تقوم"),
    ("imperf 3md", "يقومان بتحليل الخطاب", "يقومان"),
    ("imperf 3fd", "تقومان بمراجعة الحسابات", "تقومان"),
    ("imperf 3mp", "يقومون بتوزيع الموارد", "يقومون"),
    ("imperf 3fp", "يقمن بزيارة المدارس", "يقمن"),
    ("imperf 2fs", "تقومين بإصلاح النظام", "تقومين"),
    ("imperf 2mp", "تقومون بتنفيذ الأوامر", "تقومون"),
    ("imperf 1s", "أقوم بمراجعة التقرير", "أقوم"),
    ("imperf 1p", "نقوم بدراسة المشروع", "نقوم"),
    ("jussive 3ms", "لم يقم المسؤول بأي إجراء", "يقم"),
    ("jussive 3fs", "لم تقم الحكومة بأي خطوة", "تقم"),
    ("jussive 3mp", "لم يقوموا بأي محاولة", "يقوموا"),
    ("jussive 3fp", "لم يقمن بأي زيارة", "يقمن"),
    ("jussive 2ms", "لم تقم بأي مراجعة", "تقم"),
    ("jussive لا", "لا تقم بتوزيع الأوراق", "تقم"),
    ("jussive 1s", "لم أقم بأي تعديل", "أقم"),
    ("subj لن 3ms", "لن يقوم الوفد بزيارة المدينة", "يقوم"),
    ("subj أن 3ms", "يجب أن يقوم الباحث بدراسة الظاهرة", "يقوم"),
    ("subj لن 3mp", "لن يقوموا بتنفيذ المشروع", "يقوموا"),
    ("imperative ms", "قم بمراجعة النص", "قم"),
    ("imperative mp", "قوموا بتوزيع الأوراق", "قوموا"),
]


def trigger_fired_on(sentence, surface):
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    for index, word in tokens:
        if word == surface and is_qam_trigger(
            tokens, index, disambiguated, QAM_TRIGGER_LEXES, QAM_MISTAGGED_SURFACES
        ):
            return True
    return False


def any_trigger_in(sentence):
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    return any(
        is_qam_trigger(
            tokens, index, disambiguated, QAM_TRIGGER_LEXES, QAM_MISTAGGED_SURFACES
        )
        for index, _ in tokens
    )


@pytest.mark.parametrize(
    "label, sentence, surface",
    CONJUGATIONS,
    ids=[case[0] for case in CONJUGATIONS],
)
def test_real_trigger_fires_on_every_conjugation(label, sentence, surface):
    """US-1: the trigger fires on every conjugation, not only قام/قامت/يقوم/تقوم."""
    assert trigger_fired_on(sentence, surface) is True


def test_real_trigger_fires_on_the_jussive_that_the_surface_list_missed():
    """The task's motivating case — «لم يقم المسؤول بأي إجراء» was missed
    entirely because يقم is jussive. This blocks V4-6."""
    assert trigger_fired_on("لم يقم المسؤول بأي إجراء", "يقم") is True


@pytest.mark.parametrize(
    "sentence",
    [
        "لم نقم بأي إصلاح",
        "لم نقم بمراجعة التقرير",
        "نحن لم نقم بتوزيع الأوراق",
        "لا نقم بتوزيع الأوراق",
    ],
)
def test_real_trigger_fires_on_first_person_plural_jussive(sentence):
    """CAMeL tags نقم as noun/نقمة; the negation-particle correction recovers it,
    which takes conjugation coverage to 34/34."""
    assert trigger_fired_on(sentence, "نقم") is True


@pytest.mark.parametrize(
    "sentence", ["حلت بهم نقم كثيرة", "نقم الشعب على الحاكم", "النقم تتوالى عليهم"]
)
def test_real_genuine_naqmah_noun_does_not_trigger(sentence):
    """The correction is scoped by a preceding part_neg, so the real noun is
    untouched wherever it actually occurs."""
    assert any_trigger_in(sentence) is False


def test_real_the_other_verb_naqama_is_untouched():
    """ن.ق.م «to resent» is ننقم in this person, so it never collides."""
    assert any_trigger_in("لم ننقم عليهم شيئا") is False


""" the non-light-verb senses must not reach a flag """


@pytest.mark.parametrize(
    "sentence",
    [
        "قام الرجل من مكانه",
        "قامت الحرب بين البلدين",
        "يقوم النظام على مبدأ العدالة",
        "قام الطالب واقفا",
    ],
)
def test_real_other_senses_of_qam_carry_no_bi_prep_complement(sentence):
    """These are real verb uses of قام, so the lemma trigger does fire. What
    keeps them silent is that they take من/بين/على — no token carries
    prc1=bi_prep, so the V4-3 scan finds no complement."""
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)

    assert any_trigger_in(sentence)
    assert not any(entry["prc1"] == "bi_prep" for entry in disambiguated)


@pytest.mark.parametrize(
    "sentence", ["ذهب قوم إلى المدينة", "هؤلاء قوم صالحون", "قوم الرجل يسكنون القرية"]
)
def test_real_qawm_as_a_noun_does_not_trigger(sentence):
    """Accepting قوم as a lemma is only safe because the nominal use reads noun."""
    assert any_trigger_in(sentence) is False


@pytest.mark.parametrize(
    "sentence, surface",
    [("قام الباحث بحثا ميدانيا", "بحثا"), ("قام المدير بدأ العمل", "بدأ")],
)
def test_real_stem_initial_ba_is_not_a_bi_prep(sentence, surface):
    """No extra guard is needed against a stem-initial ب — it reads prc1=0."""
    tokens = preprocess(sentence)
    disambiguated = get_pos_and_pattern_in_context(tokens)
    entry = next(d for (i, w), d in zip(tokens, disambiguated) if w == surface)

    assert entry["prc1"] == "0"
