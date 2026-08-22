import pytest
from app.engine.morphology import (
    hollow_weak_letter_from_pattern,
    generate_root_candidates,
    classify_measure,
    verb_matches_measure,
    same_radical,
)

""" hollow_weak_letter_from_pattern tests """


def test_hollow_weak_letter_reads_ya_from_pattern():
    assert hollow_weak_letter_from_pattern("ق.#.م", "تَ1ْيِي3") == "ي"


def test_hollow_weak_letter_reads_waw_from_pattern():
    assert hollow_weak_letter_from_pattern("ط.#.ر", "تَ1ْوِي3") == "و"


def test_hollow_weak_letter_none_when_weak_slot_is_not_middle():
    assert hollow_weak_letter_from_pattern("ن.ه.#", "ٱِ1ْتِ2اء") is None


def test_hollow_weak_letter_none_when_pattern_keeps_placeholder_2():
    assert hollow_weak_letter_from_pattern("#.ق.ف", "تَوَ2ُّ3") is None


def test_hollow_weak_letter_none_for_quadriliteral_root():
    assert hollow_weak_letter_from_pattern("د.ه.#.ر", "تَ1َ2ْوُ4") is None


def test_hollow_weak_letter_none_when_middle_is_not_a_weak_letter():
    assert hollow_weak_letter_from_pattern("ق.#.م", "1َ2َ3") is None


def test_hollow_weak_letter_skips_leading_alif_of_mufaaala():
    """مفاعلة seats an alif ahead of the radical (مُ1ايِ3َةٌ), unlike تفعيل
    where the radical leads the slice — معاينة must still resolve to ي."""
    assert hollow_weak_letter_from_pattern("ع.#.ن", "مُ1ايِ3َةٌ") == "ي"
    assert hollow_weak_letter_from_pattern("ق.#.م", "مُ1اوَ3َةٌ") == "و"


""" same_radical tests """


def test_same_radical_matches_hamza_carriers_against_plain_hamza():
    """Arramooz stores every hamza carrier as ء in its root column while the
    verb itself spells أ/إ/آ/ئ (root ء.ن.ف, verb استأنف)."""
    for carrier in "أإآئؤء":
        assert same_radical(carrier, "ء") is True


def test_same_radical_matches_identical_plain_letters():
    assert same_radical("ن", "ن") is True


def test_same_radical_false_for_different_letters():
    assert same_radical("س", "ج") is False
    assert same_radical("أ", "ع") is False


""" generate_root_candidates tests """


def test_generate_root_candidates_returns_single_root_when_no_weak_slot():
    assert generate_root_candidates("ن.ه.ك", "ٱِ1ْتِ2ا3") == ["نهك"]


def test_generate_root_candidates_resolves_hollow_root_to_one_candidate():
    assert generate_root_candidates("ط.#.ر", "تَ1ْوِي3") == ["طور"]


def test_generate_root_candidates_tries_all_weak_letters_when_unresolved():
    candidates = generate_root_candidates("ن.ه.#", "ٱِ1ْتِ2اء")

    assert candidates == ["نهو", "نهي", "نهء"]


def test_generate_root_candidates_without_pattern_falls_back_to_all_weak_letters():
    assert generate_root_candidates("ق.#.م") == ["قوم", "قيم", "قءم"]


""" classify_measure tests """


@pytest.mark.parametrize(
    "raw_pattern, expected",
    [
        ("ٱِسْتِ1ا3َةٌ", "X"),
        ("ٱِ1ْتِ2اء", "VIII"),
        ("إِ1ْ2اء", "IV"),
        ("تَ1َوُّ3", "V"),
        ("تَ1ا2ِي", "VI"),
        ("تَ1ْيِي3", "II"),
        ("1ُيّا3", "I"),
        ("مُ1ا2َ3َةٌ", "III"),
        ("مَ1ا2ِ3ُهُ", "III"),
        ("ٱِنْ1ِ2ا3", "VII"),
        ("ٱِ1ْدِ2ا3", "VIII"),
        ("ٱِ1ْطِ2ا3", "VIII"),
    ],
)
def test_classify_measure(raw_pattern, expected):
    assert classify_measure(raw_pattern) == expected


def test_classify_measure_vii_wins_over_generic_alif_branch():
    """انفعال must not fall into the IV/VIII branch that any ٱِ pattern hits."""
    assert classify_measure("ٱِنْ1ِ2ا3") == "VII"


def test_classify_measure_iii_not_confused_with_other_meem_nouns():
    """مفعل/مفعول nouns carry a sukun after the first radical, not an alif."""
    assert classify_measure("مَ1ْ2َ3ٍ") != "III"
    assert classify_measure("مَ1ْ2ُو3") != "III"


""" verb_matches_measure tests """


def test_verb_matches_measure_ii_requires_shadda():
    row = {"unvocalized": "قيم", "vocalized": "قَيَّمَ"}

    assert verb_matches_measure(row, "II") is True


def test_verb_matches_measure_ii_rejects_unshadda_verb():
    row = {"unvocalized": "قام", "vocalized": "قَامَ"}

    assert verb_matches_measure(row, "II") is False


def test_verb_matches_measure_i_rejects_shadda_verb():
    row = {"unvocalized": "غيب", "vocalized": "غَيَّبَ"}

    assert verb_matches_measure(row, "I") is False


def test_verb_matches_measure_i_accepts_unshadda_verb():
    row = {"unvocalized": "غاب", "vocalized": "غَابَ"}

    assert verb_matches_measure(row, "I") is True


def test_verb_matches_measure_x_requires_ist_prefix():
    assert verb_matches_measure(
        {"unvocalized": "استراح", "vocalized": "اِسْتَرَاحَ"}, "X"
    ) is True
    assert verb_matches_measure(
        {"unvocalized": "راح", "vocalized": "رَاحَ"}, "X"
    ) is False


def test_verb_matches_measure_unclear_form_does_not_filter():
    row = {"unvocalized": "تدهور", "vocalized": "تَدَهْوَرَ"}

    assert verb_matches_measure(row, "V_or_VI_unclear") is True


def test_verb_matches_measure_iii_accepts_faaala_shape():
    row = {"unvocalized": "راجع", "vocalized": "رَاجَعَ", "root": "رجع"}

    assert verb_matches_measure(row, "III") is True


def test_verb_matches_measure_iii_rejects_bare_triliteral():
    row = {"unvocalized": "رجع", "vocalized": "رَجَعَ", "root": "رجع"}

    assert verb_matches_measure(row, "III") is False


def test_verb_matches_measure_vii_accepts_infaala_shape():
    row = {"unvocalized": "انقسم", "vocalized": "اِنْقَسَمَ", "root": "قسم"}

    assert verb_matches_measure(row, "VII") is True


def test_verb_matches_measure_iv_rejects_form_vii_verb():
    """انغلق is form VII — it opens with a plain alif and would otherwise pass
    the IV filter, then beat أغلق on length against the masdar إغلاق."""
    row = {"unvocalized": "انغلق", "vocalized": "اِنْغَلَقَ", "root": "غلق"}

    assert verb_matches_measure(row, "IV") is False


def test_verb_matches_measure_viii_rejects_form_x_verb_via_root():
    """استجمع has ت at index 2 like a form VIII verb, but its first radical
    sits at index 3 — only the root exposes that it is form X."""
    row = {"unvocalized": "استجمع", "vocalized": "اِسْتَجْمَعَ", "root": "جمع"}

    assert verb_matches_measure(row, "VIII") is False


def test_verb_matches_measure_viii_accepts_matching_root():
    row = {"unvocalized": "اجتمع", "vocalized": "اِجْتَمَعَ", "root": "جمع"}

    assert verb_matches_measure(row, "VIII") is True


def test_verb_matches_measure_iv_accepts_ta_as_second_radical():
    """أنتج has ت as a real second radical, not form VIII's infix — the root
    holds that ت, which is what separates the two cases."""
    row = {"unvocalized": "أنتج", "vocalized": "أَنْتَجَ", "root": "نتج"}

    assert verb_matches_measure(row, "IV") is True


def test_verb_matches_measure_iv_rejects_form_iii_of_hamza_root():
    """آخذ is form III of a hamza-initial root; it must not read as form IV."""
    row = {"unvocalized": "آخذ", "vocalized": "آخَذَ", "root": "ءخذ"}

    assert verb_matches_measure(row, "IV") is False


def test_verb_matches_measure_x_matches_hamza_radical_across_spellings():
    """استأنف spells its first radical أ while the root column stores ء."""
    row = {"unvocalized": "استأنف", "vocalized": "اِسْتَأْنَفَ", "root": "ءنف"}

    assert verb_matches_measure(row, "X") is True


@pytest.mark.parametrize(
    "verb, vocalized, root",
    [
        ("ازدحم", "اِزْدَحَمَ", "زحم"),
        ("اضطرب", "اِضْطَرَبَ", "ضرب"),
        ("اصطدم", "اِصْطَدَمَ", "صدم"),
    ],
)
def test_verb_matches_measure_viii_accepts_assimilated_infix(verb, vocalized, root):
    """Form VIII's ت assimilates to د after ز/د/ذ and ط after the emphatics."""
    row = {"unvocalized": verb, "vocalized": vocalized, "root": root}

    assert verb_matches_measure(row, "VIII") is True


def test_verb_matches_measure_viii_rejects_wrong_assimilated_infix():
    """A ت where the radical demands د is not a form VIII verb of that root."""
    row = {"unvocalized": "ازتحم", "vocalized": "اِزْتَحَمَ", "root": "زحم"}

    assert verb_matches_measure(row, "VIII") is False


def test_verb_matches_measure_accepts_any_of_a_multi_root_entry():
    """أفاد is filed under 'فود;فيد'; either may be the root that matched."""
    row = {"unvocalized": "استفاد", "vocalized": "اِسْتَفَادَ", "root": "فود;فيد"}

    assert verb_matches_measure(row, "X") is True


def test_verb_matches_measure_viii_accepts_assimilated_verb():
    """اتخذ assimilates its first radical into the ت, so index 1 holds no
    radical to match against the root."""
    row = {"unvocalized": "اتخذ", "vocalized": "اِتَّخَذَ", "root": "ءخذ"}

    assert verb_matches_measure(row, "VIII") is True




def test_verb_matches_measure_i_accepts_contracted_geminate():
    """حَلَّ spells حل — two letters unvocalized — and its shadda marks the
    doubled radical, not measure II."""
    row = {"unvocalized": "حل", "vocalized": "حَلَّ", "root": "حلل"}

    assert verb_matches_measure(row, "I") is True


def test_verb_matches_measure_i_still_rejects_shadda_on_three_letters():
    row = {"unvocalized": "قيم", "vocalized": "قَيَّمَ", "root": "قيم"}

    assert verb_matches_measure(row, "I") is False


def test_classify_measure_viii_when_second_radical_is_ta():
    """افتتاح patterns as 'ٱِ1ْ2ِتا3' — the infix ت lands after the second
    radical slot, so the usual تِ probe misses it."""
    assert classify_measure("ٱِ1ْ2ِتا3") == "VIII"
