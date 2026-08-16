import pytest
from app.engine.derivation import (
    derive_base_verb,
    get_forced_base_verb,
    is_trusted_derivation,
)

""" derive_base_verb — real CAMeL + Arramooz output """

WEAK_ROOT_CASES = {
    "ارتقاء": "ارتقى",
    "تعافي": "تعافى",
    "استقالة": "استقال",
    "استدعاء": "استدعى",
    "ابتلاء": "ابتلى",
    "تحول": "تحول",
    "تأخر": "تأخر",
    "تدهور": "تدهور",
    "توقف": "توقف",
    "تقييم": "قيم",
    "توثيق": "وثق",
    "استراحة": "استراح",
    "استجابة": "استجاب",
    "استعانة": "استعان",
    "استيراد": "استورد",
    "تضاؤل": "تضاءل",
    "تزايد": "تزايد",
    "تناول": "تناول",
    "تداول": "تداول",
    "وصول": "وصل",
    "وقوع": "وقع",
    "غياب": "غاب",
    "إنشاء": "أنشأ",
    "إيقاف": "أوقف",
    "إلغاء": "ألغى",
    "تغيير": "غير",
    "تطوير": "طور",
    "توزيع": "وزع",
    "اختيار": "اختار",
    "انتهاء": "انتهى",
    "انتهاك": "انتهك",
}


@pytest.mark.parametrize("masdar, expected", sorted(WEAK_ROOT_CASES.items()))
def test_real_derive_base_verb_on_weak_roots(masdar, expected):
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


def test_real_derive_base_verb_resolves_hollow_measure_ii_uniquely():
    """تقييم and تطوير share a root skeleton shape and differ only in the weak
    middle radical — reading it off the pattern must resolve both outright."""
    assert derive_base_verb("تقييم") == ("قيم", "unique_match")
    assert derive_base_verb("تطوير") == ("طور", "unique_match")


def test_real_derive_base_verb_uses_stem_tiebreak_for_ta_marbuta_masdar():
    assert derive_base_verb("استراحة") == ("استراح", "stem_disambiguated")


@pytest.mark.parametrize(
    "masdar, expected",
    [
        ("مراجعة", "راجع"),
        ("مناقشة", "ناقش"),
        ("معالجة", "عالج"),
        ("مقارنة", "قارن"),
        ("متابعة", "تابع"),
        ("مساعدة", "ساعد"),
    ],
)
def test_real_derive_base_verb_on_measure_iii(masdar, expected):
    """مفاعلة masdars used to fall through to measure I and return the bare
    triliteral (مراجعة → رجع instead of راجع)."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [
        ("انسحاب", "انسحب"),
        ("اندماج", "اندمج"),
        ("انخفاض", "انخفض"),
        ("انقسام", "انقسم"),
    ],
)
def test_real_derive_base_verb_on_measure_vii(masdar, expected):
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [("إغلاق", "أغلق"), ("اجتماع", "اجتمع"), ("احتلال", "احتل"), ("اتخاذ", "اتخذ")],
)
def test_real_derive_base_verb_does_not_cross_measure_families(masdar, expected):
    """Verbs of a neighbouring measure used to survive the filter and then win
    the length tiebreak (إغلاق → انغلق, اجتماع → استجمع)."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [
        ("إنتاج", "أنتج"),
        ("استئناف", "استأنف"),
        ("استئجار", "استأجر"),
        ("معاينة", "عاين"),
    ],
)
def test_real_derive_base_verb_on_previously_failing_shapes(masdar, expected):
    """ت as a real radical (أنتج), hamza spelled أ against a ء root, and the
    مفاعلة alif each used to defeat derivation entirely."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [
        ("استفادة", "استفاد"),
        ("إفادة", "أفاد"),
        ("إزاحة", "أزاح"),
        ("اتحاد", "اتحد"),
    ],
)
def test_real_derive_base_verb_finds_multi_root_entries(masdar, expected):
    """Arramooz files a few verbs under several ';'-joined roots at once; an
    exact-match lookup missed them entirely."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [("ازدحام", "ازدحم"), ("اضطراب", "اضطرب"), ("اصطدام", "اصطدم")],
)
def test_real_derive_base_verb_on_assimilated_form_viii(masdar, expected):
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize(
    "masdar, expected",
    [
        ("الاتفاق", "اتفق"),
        ("الإعلان", "أعلن"),
        ("المراجعة", "راجع"),
        ("الاستخدام", "استخدم"),
        ("الانسحاب", "انسحب"),
        ("الاضطراب", "اضطرب"),
    ],
)
def test_real_derive_base_verb_strips_definite_article(masdar, expected):
    """تم + الـ + masdar is at least as common as the bare form. The article
    rides along in the pattern (الاتفاق → 'الٱِتِّ2ا3ِ'), hiding the measure's
    opening marks and making every such word read as measure I."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


@pytest.mark.parametrize("masdar, expected", [("التزام", "التزم"), ("التقاء", "التقى")])
def test_real_derive_base_verb_keeps_alif_lam_that_is_root_material(masdar, expected):
    """التزام opens with ا and ل that belong to the word, not a determiner —
    stripping them by surface spelling would break it. The pattern is what
    distinguishes the two cases."""
    verb, _ = derive_base_verb(masdar)

    assert verb == expected


def test_real_derive_base_verb_hamza_root_does_not_pick_form_iii():
    """Regression: widening the form IV prefixes to include آ let آخذ (form
    III of ء.خ.ذ) win, turning a correct أخذ into a wrong آخذ."""
    verb, _ = derive_base_verb("أخذ")

    assert verb == "أخذ"


def test_real_derive_base_verb_collapses_duplicate_rows_to_unique_match():
    """Arramooz lists خرج several times over; identical spellings are one
    answer, not an ambiguity to report."""
    assert derive_base_verb("خروج") == ("خرج", "unique_match")


@pytest.mark.xfail(
    reason="known limitation: form VIII with س as first radical (استلم) is "
    "spelled identically to form X (استسلم) and shares its root, so neither "
    "shape nor root separates them; length proximity then picks the longer",
    strict=True,
)
def test_real_derive_base_verb_form_viii_with_seen_first_radical():
    verb, _ = derive_base_verb("استلام")

    assert verb == "استلم"


""" get_forced_base_verb tests """


def test_get_forced_base_verb_returns_hand_verified_verb():
    forced = {"استلام": "استلم"}

    assert get_forced_base_verb("استلام", forced) == "استلم"


def test_get_forced_base_verb_matches_definite_article_form():
    """«تم الاستلام» and «تم استلام» must hit the same single entry."""
    forced = {"استلام": "استلم"}

    assert get_forced_base_verb("الاستلام", forced) == "استلم"


def test_get_forced_base_verb_returns_none_when_absent():
    assert get_forced_base_verb("اتفاق", {"استلام": "استلم"}) is None


def test_get_forced_base_verb_empty_list():
    assert get_forced_base_verb("استلام", {}) is None


def test_get_forced_base_verb_alif_lam_stripping_does_not_false_match():
    """التزام opens with ا and ل that are root material; stripping them must
    not accidentally hit an unrelated entry."""
    assert get_forced_base_verb("التزام", {"تزام": "wrong"}) == "wrong"
    assert get_forced_base_verb("التزام", {"استلام": "استلم"}) is None


def test_real_forced_verb_overrides_the_wrong_derivation():
    """Unforced, derive_base_verb returns استسلم and is withheld, so the word
    never flags. The forced entry short-circuits that and is trusted."""
    verb, status = derive_base_verb("استلام")
    assert verb == "استسلم"
    assert is_trusted_derivation(status) is False

    verb, status = derive_base_verb("استلام", {"استلام": "استلم"})
    assert verb == "استلم"
    assert status == "forced"
    assert is_trusted_derivation(status) is True


def test_real_forced_verb_applies_to_definite_article_form():
    verb, status = derive_base_verb("الاستلام", {"استلام": "استلم"})

    assert (verb, status) == ("استلم", "forced")


def test_real_forced_verbs_does_not_disturb_words_absent_from_it():
    """A forced list must only affect its own entries."""
    assert derive_base_verb("اتفاق", {"استلام": "استلم"}) == ("اتفق", "unique_match")


def test_derive_base_verb_without_forced_list_keeps_old_signature():
    """The parameter is optional — existing callers keep working."""
    assert derive_base_verb("اتفاق") == ("اتفق", "unique_match")


def test_is_trusted_derivation_true_for_forced():
    assert is_trusted_derivation("forced") is True


""" is_trusted_derivation tests """


@pytest.mark.parametrize(
    "status",
    ["unique_match", "shadda_disambiguated", "stem_disambiguated", "still_ambiguous"],
)
def test_is_trusted_derivation_true_for_trusted_statuses(status):
    assert is_trusted_derivation(status) is True


def test_is_trusted_derivation_false_for_length_tiebreak():
    """Length proximity is the only tiebreak that has produced a wrong base
    verb, so it must not reach the flag decision."""
    assert is_trusted_derivation("length_disambiguated") is False


@pytest.mark.parametrize(
    "status", ["no_camel_analysis", "no_arramooz_root_match", "no_measure_match"]
)
def test_is_trusted_derivation_false_for_failures(status):
    assert is_trusted_derivation(status) is False


def test_is_trusted_derivation_defaults_closed_for_unknown_status():
    """A status added later must be opted in deliberately, not trusted by
    default just because it is not on a rejection list."""
    assert is_trusted_derivation("some_future_tiebreak") is False


def test_real_wrong_derivation_is_not_trusted():
    """The one known-wrong derivation in the sampled set must be withheld by
    the confidence policy rather than reaching the transitivity lookup."""
    _, status = derive_base_verb("استلام")

    assert is_trusted_derivation(status) is False


def test_real_derive_base_verb_reports_unresolved_ambiguity():
    """وصول lands on the right verb only because of Arramooz row order — the
    status must say so rather than presenting it as a resolved derivation."""
    verb, status = derive_base_verb("وصول")

    assert verb == "وصل"
    assert status == "still_ambiguous"
