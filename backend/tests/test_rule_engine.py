import pytest
from unittest.mock import patch

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import (
    find_bshakl_matches,
    find_tam_matches,
    masdar_target_index,
    next_target_index,
    analyze,
)

""" next_target_index tests """


def test_next_target_index_takes_the_following_word():
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "جميل")]

    assert next_target_index(tokens, 1) == 2


def test_next_target_index_skips_non_alphabetic_tokens():
    tokens = [(0, "بشكل"), (1, "100%"), (2, "عادل")]

    assert next_target_index(tokens, 0) == 2


def test_next_target_index_gives_up_beyond_the_skip_limit():
    tokens = [(0, "بشكل"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "عادل")]

    assert next_target_index(tokens, 0) is None


def test_next_target_index_none_when_trigger_is_last():
    tokens = [(0, "كتب"), (1, "المقال"), (2, "بشكل")]

    assert next_target_index(tokens, 2) is None


def test_next_target_index_skips_a_dash_aside():
    """«بشكل - ولله الحمد - كبير» — the target is كبير, not ولله."""
    tokens = list(enumerate(["بشكل", "-", "ولله", "الحمد", "-", "كبير"]))

    assert next_target_index(tokens, 0) == 5


def test_next_target_index_skips_a_bracketed_aside():
    tokens = list(enumerate(["بشكل", "(", "تقريبا", ")", "كامل"]))

    assert next_target_index(tokens, 0) == 4


def test_next_target_index_skips_a_comma_aside():
    tokens = list(enumerate(["بشكل", "،", "فيما", "يبدو", "،", "جيد"]))

    assert next_target_index(tokens, 0) == 5


def test_next_target_index_treats_an_unclosed_delimiter_as_plain_punctuation():
    """A lone comma is not an aside — «بشكل ، كبير» still reaches كبير."""
    tokens = list(enumerate(["بشكل", "،", "كبير"]))

    assert next_target_index(tokens, 0) == 2


""" find_bshakl_matches tests """


def _bshakl_rules():
    return {"trigger_word": "بشكل"}


def _bshakl_whitelist(**overrides):
    base = {
        "whitelisted_lemmas": [],
        "whitelisted_phrases": [],
        "force_excluded_lemmas": [],
    }
    base.update(overrides)
    return base


def _descriptor(lex="جميل", pos="adj", prc0="0"):
    return {"pos": pos, "pattern": "", "lex": lex, "prc0": prc0, "prc1": "0", "prc2": "0"}


def test_find_bshakl_matches_flags_a_descriptor():
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "جميل")]
    disambiguated = [_descriptor(pos="verb"), _descriptor(pos="noun"), _descriptor()]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(), tokens, disambiguated
    )

    assert [m["flagged_phrase"] for _, m in matches] == ["بشكل جميل"]


def test_find_bshakl_matches_keeps_the_prefix_in_the_phrase():
    """«وبشكل ملحوظ» should report what the text actually says."""
    tokens = [(0, "تحسن"), (1, "وبشكل"), (2, "ملحوظ")]
    disambiguated = [_descriptor(pos="verb"), _descriptor(pos="noun"), _descriptor()]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(), tokens, disambiguated
    )

    assert matches[0][1]["flagged_phrase"] == "وبشكل ملحوظ"


def test_find_bshakl_matches_skips_whitelisted_shape_lemma():
    tokens = [(0, "بشكل"), (1, "دائري")]
    disambiguated = [_descriptor(pos="noun"), _descriptor(lex="دائر")]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(whitelisted_lemmas=["دائر"]),
        tokens, disambiguated,
    )

    assert matches == []


def test_find_bshakl_matches_skips_whitelisted_phrase():
    tokens = [(0, "بشكل"), (1, "شبه"), (2, "منحرف")]
    disambiguated = [_descriptor(pos="noun"), _descriptor(), _descriptor()]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(whitelisted_phrases=["شبه منحرف"]),
        tokens, disambiguated,
    )

    assert matches == []


def test_find_bshakl_matches_skips_force_excluded_lemma():
    tokens = [(0, "بشكل"), (1, "واحد")]
    disambiguated = [_descriptor(pos="noun"), _descriptor(lex="واحد")]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(force_excluded_lemmas=["واحد"]),
        tokens, disambiguated,
    )

    assert matches == []


def test_find_bshakl_matches_skips_non_descriptor():
    tokens = [(0, "بشكل"), (1, "من")]
    disambiguated = [_descriptor(pos="noun"), _descriptor(pos="prep")]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(), tokens, disambiguated
    )

    assert matches == []


def test_find_bshakl_matches_finds_every_trigger():
    tokens = list(enumerate(["بشكل", "رائع", "و", "وبشكل", "كبير"]))
    disambiguated = [
        _descriptor(pos="noun"), _descriptor(), _descriptor(pos="conj"),
        _descriptor(pos="noun"), _descriptor(),
    ]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(), tokens, disambiguated
    )

    assert [index for index, _ in matches] == [0, 3]


def test_find_bshakl_matches_no_trigger_present():
    tokens = [(0, "الجو"), (1, "جميل")]
    disambiguated = [_descriptor(pos="noun"), _descriptor()]

    matches = find_bshakl_matches(
        _bshakl_rules(), _bshakl_whitelist(), tokens, disambiguated
    )

    assert matches == []


""" analyze — orchestration """


RULES_PATH = "fake/rules.json"
WHITELIST_PATH = "fake/whitelist.json"


def _base_whitelist(**overrides):
    base = {
        "whitelisted_lemmas": [],
        "whitelisted_phrases": [],
        "force_excluded_lemmas": [],
    }
    base.update(overrides)
    return base


def test_analyze_returns_clean_response_for_empty_text():
    with patch("app.engine.rule_engine.reader", side_effect=[{}, {}]), patch(
        "app.engine.rule_engine.preprocess", return_value=[]
    ), patch("app.engine.rule_engine.get_pos_and_pattern_in_context") as mock_disambig:

        result = analyze(RULES_PATH, WHITELIST_PATH, "")

    assert result == {"flagged": False, "matches": []}
    mock_disambig.assert_not_called()


def test_analyze_skips_the_model_when_no_trigger_and_no_tam_rule():
    """The بشكل scan is a plain string test, so with no بشكل in the text and
    no تمّ rule configured there is nothing worth loading CAMeL for."""
    rules = {"trigger_word": "بشكل"}
    tokens = [(0, "الجو"), (1, "جميل")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _base_whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context"
    ) as mock_disambig:

        result = analyze(RULES_PATH, WHITELIST_PATH, "الجو جميل")

    assert result == {"flagged": False, "matches": []}
    mock_disambig.assert_not_called()


def test_analyze_still_runs_the_model_for_tam_when_no_bshakl_present():
    """تمّ is matched on lemma, so it cannot be ruled out before the model."""
    rules = {"trigger_word": "بشكل", "tam_trigger_lex": "تم"}
    tokens = [(0, "تم"), (1, "إغلاق")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _base_whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context", return_value=[{}, {}]
    ) as mock_disambig, patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[]
    ):

        analyze(RULES_PATH, WHITELIST_PATH, "تم إغلاق")

    mock_disambig.assert_called_once()


def test_analyze_merges_both_rules_in_reading_order():
    rules = {"trigger_word": "بشكل", "tam_trigger_lex": "تم"}
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "بشكل"), (3, "رائع")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _base_whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[{}, {}, {}, {}],
    ), patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[(2, "BSHAKL")]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[(0, "TAM")]
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "تم إغلاق بشكل رائع")

    assert result == {"flagged": True, "matches": ["TAM", "BSHAKL"]}


def test_analyze_wraps_matches_in_the_response_shape():
    rules = {"trigger_word": "بشكل"}
    tokens = [(0, "بشكل"), (1, "رائع")]

    with patch(
        "app.engine.rule_engine.reader", side_effect=[rules, _base_whitelist()]
    ), patch("app.engine.rule_engine.preprocess", return_value=tokens), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context", return_value=[{}, {}]
    ), patch(
        "app.engine.rule_engine.find_bshakl_matches", return_value=[(0, "MATCH")]
    ), patch(
        "app.engine.rule_engine.find_tam_matches", return_value=[]
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "بشكل رائع")

    assert result == {"flagged": True, "matches": ["MATCH"]}



""" find_tam_matches tests """


def _tam_rules(**overrides):
    base = {"trigger_word": "بشكل", "flagged_patterns": [], "tam_trigger_lex": "تم"}
    base.update(overrides)
    return base


def _tam_whitelist(**overrides):
    base = _base_whitelist()
    base.update(
        {
            "force_derived_verbs": {},
            "force_intransitive_verbs": [],
            "force_not_masdar": [],
            "force_intransitive_masdars": [],
        }
    )
    base.update(overrides)
    return base


def test_find_tam_matches_flags_transitive_masdar():
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "إِ12ا3", "lex": "إغلاق"},
        {"pos": "noun", "pattern": "ال123", "lex": "باب"},
    ]

    with patch(
        "app.engine.rule_engine.derive_base_verb", return_value=("أغلق", "unique_match")
    ), patch("app.engine.rule_engine.is_transitive_verb", return_value=True):

        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert len(matches) == 1
    assert matches[0][1]["flagged_phrase"] == "تم إغلاق"


def test_find_tam_matches_passes_intransitive_masdar():
    tokens = [(0, "تم"), (1, "خروج")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "12و3", "lex": "خروج"},
    ]

    with patch(
        "app.engine.rule_engine.derive_base_verb", return_value=("خرج", "unique_match")
    ), patch("app.engine.rule_engine.is_transitive_verb", return_value=False):

        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches == []


def test_find_tam_matches_withholds_untrusted_derivation():
    """An untrusted derivation must not reach the transitivity lookup at all."""
    tokens = [(0, "تم"), (1, "استلام")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "ٱِ12ا3", "lex": "استلام"},
    ]

    with patch(
        "app.engine.rule_engine.derive_base_verb",
        return_value=("استسلم", "length_disambiguated"),
    ), patch("app.engine.rule_engine.is_transitive_verb") as mock_transitive:

        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches == []
    mock_transitive.assert_not_called()


def test_find_tam_matches_ignores_nouns_ending_in_the_trigger_letters():
    tokens = [(0, "خاتم"), (1, "الذهب")]
    disambiguated = [
        {"pos": "noun", "pattern": "1ا23", "lex": "خاتم"},
        {"pos": "noun", "pattern": "ال123", "lex": "ذهب"},
    ]

    with patch("app.engine.rule_engine.derive_base_verb") as mock_derive:
        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches == []
    mock_derive.assert_not_called()


def test_find_tam_matches_skips_non_alphabetic_tokens():
    tokens = [(0, "تم"), (1, "%50"), (2, "إغلاق")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "", "lex": "%50"},
        {"pos": "noun", "pattern": "إِ12ا3", "lex": "إغلاق"},
    ]

    with patch(
        "app.engine.rule_engine.derive_base_verb", return_value=("أغلق", "unique_match")
    ), patch("app.engine.rule_engine.is_transitive_verb", return_value=True):

        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches[0][1]["flagged_phrase"] == "تم إغلاق"


def test_find_tam_matches_returns_nothing_when_rule_not_configured():
    """Without tam_trigger_lex the rule is simply off — v1-only configs must
    keep working."""
    tokens = [(0, "تم"), (1, "إغلاق")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "إِ12ا3", "lex": "إغلاق"},
    ]

    matches = find_tam_matches(
        {"trigger_word": "بشكل"}, _tam_whitelist(), tokens, disambiguated
    )

    assert matches == []


def test_find_tam_matches_passes_force_lists_through():
    tokens = [(0, "تم"), (1, "استلام")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"},
        {"pos": "noun", "pattern": "ٱِ12ا3", "lex": "استلام"},
    ]
    whitelist = _tam_whitelist(
        force_derived_verbs={"استلام": "استلم"}, force_intransitive_verbs=["خرج"]
    )

    with patch(
        "app.engine.rule_engine.derive_base_verb", return_value=("استلم", "forced")
    ) as mock_derive, patch(
        "app.engine.rule_engine.is_transitive_verb", return_value=True
    ) as mock_transitive:

        find_tam_matches(_tam_rules(), whitelist, tokens, disambiguated)

    mock_derive.assert_called_once_with("استلام", {"استلام": "استلم"})
    mock_transitive.assert_called_once_with("استلم", ["خرج"])


""" analyze — both rules in one response """


def test_real_analyze_flags_tam_with_transitive_masdar():
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


def test_real_analyze_passes_tam_with_intransitive_masdar():
    result = analyze(rules_path, whitelist_path, "تم خروج الفريق")

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_returns_both_rules_in_one_list():
    """US-1: بشكل and تمّ matches share a single unified response."""
    result = analyze(
        rules_path, whitelist_path, "الجو جميل بشكل رائع وتم تنفيذ العمل"
    )

    phrases = [m["flagged_phrase"] for m in result["matches"]]
    assert "بشكل رائع" in phrases
    assert "وتم تنفيذ" in phrases


def test_real_analyze_does_not_flag_noun_ending_in_trigger_letters():
    result = analyze(rules_path, whitelist_path, "اشترى خاتم الذهب")

    assert result == {"flagged": False, "matches": []}


""" waw chain in find_tam_matches """


def test_find_tam_matches_passes_waw_chain_without_deriving():
    """A و-chain never flags, so derivation must not even run."""
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "والمراجعة")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم", "prc1": "0", "prc2": "0"},
        {"pos": "noun", "pattern": "ت12ي3", "lex": "تدقيق", "prc1": "0", "prc2": "0"},
        {"pos": "noun", "pattern": "م1ا23", "lex": "مراجعة", "prc1": "0", "prc2": "wa_part"},
    ]

    with patch("app.engine.rule_engine.derive_base_verb") as mock_derive:
        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches == []
    mock_derive.assert_not_called()


def test_real_analyze_passes_waw_chain():
    result = analyze(rules_path, whitelist_path, "تم التدقيق والمراجعة")

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_still_flags_when_a_verb_opens_a_new_clause():
    """«تم إغلاق الباب وذهب الرجل» — the و introduces a clause with its own
    verb, so it is not chaining the masdar."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب وذهب الرجل.")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


def test_real_analyze_passes_a_chain_whose_members_carry_objects():
    """REVERTED 2026-08-28 (§2.3): a مصدر series is فصيح however its objects are
    arranged. This asserted a flag between 2026-08-26 and 2026-08-28."""
    result = analyze(
        rules_path,
        whitelist_path,
        "تم مراجعة التقارير، وتدقيق الحسابات، واعتماد الميزانية.",
    )

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_flags_masdars_sharing_one_object():
    """«تم إغلاق وفتح الباب» — قاعدة 2026-08-28: مصادر sharing one مضاف إليه is
    عرنجي and grammatically wrong. This asserted silence until then."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق وفتح الباب")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


""" masdar-vs-regular-noun gate """


def test_find_tam_matches_skips_plain_noun_without_deriving():
    """A plain noun is not an Arabized passive, so derivation must not run."""
    tokens = [(0, "تم"), (1, "البيت")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم", "prc2": "0"},
        {"pos": "noun", "pattern": "ال1َيْ3", "lex": "بيت", "prc2": "0"},
    ]

    with patch("app.engine.rule_engine.is_masdar", return_value=False), patch(
        "app.engine.rule_engine.derive_base_verb"
    ) as mock_derive:
        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches == []
    mock_derive.assert_not_called()


def test_find_tam_matches_proceeds_when_masdar_status_unknown():
    """None means Arramooz has no row; absence must not suppress a real flag."""
    tokens = [(0, "تم"), (1, "حذف")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم", "prc2": "0"},
        {"pos": "noun", "pattern": "1َ2ْ3", "lex": "حذف", "prc2": "0"},
    ]

    with patch("app.engine.rule_engine.is_masdar", return_value=None), patch(
        "app.engine.rule_engine.derive_base_verb", return_value=("حذف", "unique_match")
    ), patch("app.engine.rule_engine.is_transitive_verb", return_value=True):
        matches = find_tam_matches(_tam_rules(), _tam_whitelist(), tokens, disambiguated)

    assert matches[0][1]["flagged_phrase"] == "تم حذف"


def test_real_analyze_passes_plain_noun_after_tam():
    result = analyze(rules_path, whitelist_path, "تم الأمر بسرعة")

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_passes_valid_intransitive_masdar_sentence():
    result = analyze(rules_path, whitelist_path, "تم الاتفاق على البند")

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_still_flags_measure_one_masdar():
    """فتح is a real masdar sharing its shape with plain nouns — the noun gate
    must not suppress it."""
    result = analyze(rules_path, whitelist_path, "تم فتح الباب")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم فتح"]


def test_find_tam_matches_skips_force_intransitive_masdar_before_deriving():
    tokens = [(0, "تم"), (1, "العدول")]
    disambiguated = [
        {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم", "prc2": "0"},
        {"pos": "noun", "pattern": "ال1ُ2ُو3", "lex": "عدول", "prc2": "0"},
    ]
    whitelist = _tam_whitelist(force_intransitive_masdars=["عدول"])

    with patch("app.engine.rule_engine.is_masdar", return_value=True), patch(
        "app.engine.rule_engine.derive_base_verb"
    ) as mock_derive:
        matches = find_tam_matches(_tam_rules(), whitelist, tokens, disambiguated)

    assert matches == []
    mock_derive.assert_not_called()


def test_real_analyze_passes_force_intransitive_masdar():
    result = analyze(rules_path, whitelist_path, "تم العدول عن القرار السابق.")

    assert result == {"flagged": False, "matches": []}


def test_real_analyze_still_flags_the_colliding_sibling_masdar():
    """عدول is overridden, تعديل must not be — both derive to «عدل»."""
    result = analyze(rules_path, whitelist_path, "تم تعديل النظام.")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم تعديل"]


""" response shape and ordering """


def test_real_analyze_always_returns_the_same_shape():
    flagged = analyze(rules_path, whitelist_path, "تم إغلاق الباب.")
    clean = analyze(rules_path, whitelist_path, "الجو جميل.")

    assert set(flagged) == set(clean) == {"flagged", "matches"}
    assert flagged["flagged"] is True and clean["flagged"] is False
    assert isinstance(flagged["matches"], list)
    assert clean["matches"] == []


def test_real_analyze_labels_which_rule_matched():
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب بشكل رائع.")

    assert {m["rule"] for m in result["matches"]} == {"تم", "بشكل"}


def test_real_analyze_returns_matches_in_reading_order():
    """A بشكل hit after a تمّ hit must not be reordered ahead of it."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب بشكل رائع.")

    assert [m["rule"] for m in result["matches"]] == ["تم", "بشكل"]


def test_real_analyze_does_not_suppress_tam_before_a_prepositional_phrase():
    """Regression: the forward و-scan read «وبشكل» as a chain member and
    silently dropped the تمّ match."""
    result = analyze(
        rules_path, whitelist_path, "تم إغلاق الباب وبشكل رائع كتب المقال."
    )

    assert "تم إغلاق" in [m["flagged_phrase"] for m in result["matches"]]


""" intransitive overrides are keyed by masdar, not verb """


@pytest.mark.parametrize(
    "sentence, phrase",
    [
        ("تم توقيع الاتفاقية.", "تم توقيع"),
        ("تم توصيل الطلب.", "تم توصيل"),
        ("تم تخريج الدفعة.", "تم تخريج"),
        ("تم تصعيد الموقف.", "تم تصعيد"),
    ],
)
def test_real_analyze_flags_transitive_masdar_sharing_an_intransitive_verb(
    sentence, phrase
):
    """توقيع (وقّع, II, transitive) and وقوع (وقع, I, intransitive) both derive
    to «وقع», so keying the override by verb silenced the transitive one."""
    result = analyze(rules_path, whitelist_path, sentence)

    assert [m["flagged_phrase"] for m in result["matches"]] == [phrase]


@pytest.mark.parametrize("masdar", ["خروج", "دخول", "وصول", "وقوع", "صعود"])
def test_real_analyze_still_passes_the_intransitive_masdars(masdar):
    result = analyze(rules_path, whitelist_path, f"تم {masdar} اليوم.")

    assert result == {"flagged": False, "matches": []}


""" masdar_target_index — an adverbial may sit between تمّ and its masdar """


def test_masdar_target_index_takes_the_following_noun():
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب")]
    disambiguated = [_descriptor(pos="verb"), _descriptor(pos="noun"), _descriptor(pos="noun")]

    assert masdar_target_index(tokens, 0, disambiguated) == 1


def test_masdar_target_index_steps_over_an_adverbial():
    """«يتمّ حالياً إجراء الصيانة» — حالياً is tagged adj, the masdar is noun."""
    tokens = [(0, "يتم"), (1, "حاليا"), (2, "إجراء"), (3, "الصيانة")]
    disambiguated = [
        _descriptor(pos="verb"), _descriptor(pos="adj"),
        _descriptor(pos="noun"), _descriptor(pos="noun"),
    ]

    assert masdar_target_index(tokens, 0, disambiguated) == 2


def test_masdar_target_index_stops_at_a_verb():
    """«إذا تمّ العقلُ نَقَصَ الكلامُ» must not reach into the next clause."""
    tokens = [(0, "تم"), (1, "العقل"), (2, "نقص"), (3, "الكلام")]
    disambiguated = [
        _descriptor(pos="verb"), _descriptor(pos="noun"),
        _descriptor(pos="verb"), _descriptor(pos="noun"),
    ]

    assert masdar_target_index(tokens, 0, disambiguated) == 1


def test_masdar_target_index_stops_at_sentence_end():
    tokens = [(0, "تم"), (1, "."), (2, "إغلاق")]
    disambiguated = [_descriptor(pos="verb"), _descriptor(pos="punc"), _descriptor(pos="noun")]

    assert masdar_target_index(tokens, 0, disambiguated) is None


def test_masdar_target_index_falls_back_to_a_non_noun_candidate():
    """With no noun in the window the first candidate is still returned, so the
    gates downstream get their say rather than the match vanishing here."""
    tokens = [(0, "تم"), (1, "سريعا")]
    disambiguated = [_descriptor(pos="verb"), _descriptor(pos="adj")]

    assert masdar_target_index(tokens, 0, disambiguated) == 1


def test_real_analyze_finds_the_masdar_past_an_adverbial():
    result = analyze(rules_path, whitelist_path, "يتم حاليا إجراء الصيانة.")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["يتم إجراء"]


def test_real_analyze_does_not_cross_into_the_next_clause():
    result = analyze(rules_path, whitelist_path, "إذا تم العقل نقص الكلام.")

    assert result == {"flagged": False, "matches": []}


@pytest.mark.parametrize(
    "sentence, phrase",
    [("تم حذف الملف.", "تم حذف"), ("تم تقييم الأداء.", "تم تقييم")],
)
def test_real_analyze_keeps_masdars_absent_from_the_nouns_table(sentence, phrase):
    """حذف is not in Arramooz's nouns table but الملف is recorded as a masdar —
    a scan keyed on that verdict would walk past the target onto its object."""
    result = analyze(rules_path, whitelist_path, sentence)

    assert [m["flagged_phrase"] for m in result["matches"]] == [phrase]


""" alif wasla — the lexeme lookup path """


def test_real_analyze_resolves_a_connecting_alif_masdar_at_sentence_level():
    """CAMeL returns lex=ٱكتشاف for an input spelled with a plain alif. Nothing
    reads lex for this word today, but v4's table lookup will, so the fold is
    pinned down end to end rather than only in the analysis unit test."""
    result = analyze(rules_path, whitelist_path, "تم اكتشاف الخطأ.")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم اكتشاف"]


def test_real_analyze_still_flags_a_hamza_initial_masdar():
    """The fold is confined to ٱ — إغلاق must keep resolving through Arramooz,
    which stores إ faithfully and holds no row for اغلاق."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب.")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


@pytest.mark.parametrize(
    "sentence, phrases",
    [
        ("ــ قام الفريق بدراسة الظاهرة", ["قام بدراسة"]),
        ("تم إغلاق الباب ـ فورا", ["تم إغلاق"]),
        ("ــ 15 تموز: تم إغلاق الباب", ["تم إغلاق"]),
        ("١ ـ ما الحكم", []),
    ],
)
def test_real_analyze_survives_a_tatweel(sentence, phrases):
    """Tatweel (ـ, U+0640) is ordinary Arabic typography — it appeared in 5 of
    the first 3,000 sentences of a real news corpus. It used to raise
    IndexError out of /analyze."""
    result = analyze(rules_path, whitelist_path, sentence)

    assert [m["flagged_phrase"] for m in result["matches"]] == phrases
