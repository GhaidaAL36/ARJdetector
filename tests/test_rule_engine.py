from unittest.mock import patch

from app.engine.rule_engine import find_flagged_words, analyze

""" find flagged words tests """


def test_find_flagged_words_single_trigger_no_skip_needed():
    fake_tokens = [(0, "كتب"), (1, "المقال"), (2, "بشكل"), (3, "جميل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "كتب المقال بشكل جميل"
        )

    assert flagged_indices == [3]


def test_find_flagged_words_skips_single_non_alpha_token():
    fake_tokens = [(0, "بشكل"), (1, "100%"), (2, "عادل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "بشكل 100% عادل")

    assert flagged_indices == [2]
    mock_phrase.assert_called_once_with(fake_tokens, 2, [])


def test_find_flagged_words_skips_up_to_max_limit():
    fake_tokens = [(0, "بشكل"), (1, "1"), (2, "2"), (3, "عادل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ):

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "text")

    assert flagged_indices == [3]


def test_find_flagged_words_gives_up_beyond_max_skip_limit():
    fake_tokens = [(0, "بشكل"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "عادل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted"
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "text")

    assert flagged_indices == []
    mock_phrase.assert_not_called()


def test_find_flagged_words_all_non_alpha_until_end_of_tokens():
    fake_tokens = [(0, "كتب"), (1, "بشكل"), (2, "."), (3, "!")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted"
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "كتب بشكل .!")

    assert flagged_indices == []
    mock_phrase.assert_not_called()


def test_find_flagged_words_waw_prefix_variant():
    fake_tokens = [(0, "تحسن"), (1, "الوضع"), (2, "وبشكل"), (3, "ملحوظ")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "تحسن الوضع وبشكل ملحوظ"
        )

    assert flagged_indices == [3]


def test_find_flagged_words_fa_prefix_variant():
    fake_tokens = [(0, "تغير"), (1, "الأمر"), (2, "فبشكل"), (3, "مفاجئ")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "تغير الأمر فبشكل مفاجئ"
        )

    assert flagged_indices == [3]


def test_find_flagged_words_multiple_triggers_one_with_skip():
    fake_tokens = [
        (0, "الجو"),
        (1, "جميل"),
        (2, "بشكل"),
        (3, "رائع"),
        (4, "اليوم"),
        (5, "وبشكل"),
        (6, "50"),
        (7, "كبير"),
    ]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)
    ):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "الجو جميل بشكل رائع اليوم وبشكل 50 كبير"
        )

    assert flagged_indices == [3, 7]


def test_find_flagged_words_whitelisted_phrase_still_checked_at_correct_target_idx():
    fake_tokens = [(0, "هذا"), (1, "الخبز"), (2, "بشكل"), (3, "شبه"), (4, "منحرف")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": ["شبه منحرف"]}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted", return_value=(True, 2)
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "هذا الخبز بشكل شبه منحرف"
        )

    mock_phrase.assert_called_once_with(fake_tokens, 3, ["شبه منحرف"])
    assert flagged_indices == []


def test_find_flagged_words_trigger_is_last_word_no_crash():
    fake_tokens = [(0, "كتب"), (1, "المقال"), (2, "بشكل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted"
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "كتب المقال بشكل"
        )

    mock_phrase.assert_not_called()
    assert flagged_indices == []


def test_find_flagged_words_no_trigger_present():
    fake_tokens = [(0, "الجو"), (1, "جميل"), (2, "اليوم")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), patch(
        "app.engine.rule_engine.is_phrase_whitelisted"
    ) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "الجو جميل اليوم"
        )

    mock_phrase.assert_not_called()
    assert flagged_indices == []


""" analyze tests """


RULES_PATH = "fake/rules.json"
WHITELIST_PATH = "fake/whitelist.json"


def _base_whitelist(**overrides):
    base = {
        "whitelisted_lemmas": [],
        "whitelisted_phrases": [],
        "force_flagged_lemmas": [],
        "force_excluded_lemmas": [],
    }
    base.update(overrides)
    return base


def test_analyze_flags_word_via_nisba_pattern():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist()
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "جميل")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "adj", "pattern": "12ي3", "lex": "جميل"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_excluded", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_flagged", return_value=False
    ), patch(
        "app.engine.rule_engine.matches_nisba_pattern", return_value=True
    ), patch(
        "app.engine.rule_engine.matches_flagged_pattern", return_value=False
    ), patch(
        "app.engine.rule_engine.build_match", return_value="MATCH_RESULT"
    ) as mock_build, patch(
        "app.engine.rule_engine.clean_text"
    ) as mock_clean:

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل جميل")

    assert result == ["MATCH_RESULT"]
    mock_build.assert_called_once_with("بشكل", "جميل")
    mock_clean.assert_not_called()


def test_analyze_skips_whitelisted_lemma_before_force_checks():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist(whitelisted_lemmas=["دائر"])
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "دائري")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "adj", "pattern": "12ي3", "lex": "دائر"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=True
    ) as mock_whitelist, patch(
        "app.engine.rule_engine.is_force_excluded"
    ) as mock_excluded, patch(
        "app.engine.rule_engine.is_force_flagged"
    ) as mock_flagged, patch(
        "app.engine.rule_engine.matches_nisba_pattern"
    ) as mock_nisba, patch(
        "app.engine.rule_engine.matches_flagged_pattern"
    ) as mock_pattern, patch(
        "app.engine.rule_engine.build_match"
    ) as mock_build, patch(
        "app.engine.rule_engine.clean_text", return_value="CLEAN"
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل دائري")

    mock_whitelist.assert_called_once_with("دائر", ["دائر"])
    mock_excluded.assert_not_called()
    mock_flagged.assert_not_called()
    mock_nisba.assert_not_called()
    mock_pattern.assert_not_called()
    mock_build.assert_not_called()
    assert result == "CLEAN"


def test_analyze_force_excluded_skips_before_pattern_check():
    rules = {"trigger_word": "بشكل", "flagged_patterns": ["وا23"]}
    whitelist = _base_whitelist(force_excluded_lemmas=["واحد"])
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "واحد")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "adj", "pattern": "وا23", "lex": "واحد"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_excluded", return_value=True
    ) as mock_excluded, patch(
        "app.engine.rule_engine.is_force_flagged"
    ) as mock_flagged, patch(
        "app.engine.rule_engine.matches_nisba_pattern"
    ) as mock_nisba, patch(
        "app.engine.rule_engine.matches_flagged_pattern"
    ) as mock_pattern, patch(
        "app.engine.rule_engine.build_match"
    ) as mock_build, patch(
        "app.engine.rule_engine.clean_text", return_value="CLEAN"
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل واحد")

    mock_excluded.assert_called_once_with("واحد", ["واحد"])
    mock_flagged.assert_not_called()
    mock_nisba.assert_not_called()
    mock_pattern.assert_not_called()
    mock_build.assert_not_called()
    assert result == "CLEAN"


def test_analyze_force_flagged_bypasses_pos_and_pattern_checks():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist(force_flagged_lemmas=["مباشر"])
    tokens = [(0, "تحدث"), (1, "بشكل"), (2, "مباشر")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "noun", "pattern": "م12ا3", "lex": "مباشر"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_excluded", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_flagged", return_value=True
    ) as mock_flagged, patch(
        "app.engine.rule_engine.matches_nisba_pattern"
    ) as mock_nisba, patch(
        "app.engine.rule_engine.matches_flagged_pattern"
    ) as mock_pattern, patch(
        "app.engine.rule_engine.build_match", return_value="MATCH_RESULT"
    ) as mock_build, patch(
        "app.engine.rule_engine.clean_text"
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "تحدث بشكل مباشر")

    mock_flagged.assert_called_once_with("مباشر", ["مباشر"])
    mock_nisba.assert_not_called()
    mock_pattern.assert_not_called()
    mock_build.assert_called_once_with("بشكل", "مباشر")
    assert result == ["MATCH_RESULT"]


def test_analyze_no_flagged_indices_skips_disambiguator_entirely():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist()
    tokens = [(0, "الجو"), (1, "جميل")]
    flagged_indices = []

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context"
    ) as mock_disambig, patch(
        "app.engine.rule_engine.clean_text", return_value="CLEAN"
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "الجو جميل")

    mock_disambig.assert_not_called()
    assert result == "CLEAN"


def test_analyze_strips_al_prefix_from_pattern_before_matching():
    rules = {"trigger_word": "بشكل", "flagged_patterns": ["12ي3"]}
    whitelist = _base_whitelist()
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "الكبير")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "adj", "pattern": "ال12ي3", "lex": "كبير"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_excluded", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_flagged", return_value=False
    ), patch(
        "app.engine.rule_engine.matches_nisba_pattern", return_value=False
    ) as mock_nisba, patch(
        "app.engine.rule_engine.matches_flagged_pattern", return_value=True
    ) as mock_flagged, patch(
        "app.engine.rule_engine.build_match", return_value="MATCH_RESULT"
    ), patch(
        "app.engine.rule_engine.clean_text"
    ):

        analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل الكبير")

    called_info = mock_flagged.call_args[0][1]
    assert called_info["pattern"] == "12ي3"

    called_info_nisba = mock_nisba.call_args[0][0]
    assert called_info_nisba["pattern"] == "12ي3"


def test_analyze_no_match_returns_clean_text():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist()
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "شيء")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), patch(
        "app.engine.rule_engine.find_flagged_words",
        return_value=(tokens, flagged_indices),
    ), patch(
        "app.engine.rule_engine.get_pos_and_pattern_in_context",
        return_value=[None, None, {"pos": "noun", "pattern": "123", "lex": "شيء"}],
    ), patch(
        "app.engine.rule_engine.is_whitelisted_lemma", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_excluded", return_value=False
    ), patch(
        "app.engine.rule_engine.is_force_flagged", return_value=False
    ), patch(
        "app.engine.rule_engine.matches_nisba_pattern", return_value=False
    ), patch(
        "app.engine.rule_engine.matches_flagged_pattern", return_value=False
    ), patch(
        "app.engine.rule_engine.build_match"
    ) as mock_build, patch(
        "app.engine.rule_engine.clean_text", return_value="CLEAN"
    ):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل شيء")

    mock_build.assert_not_called()
    assert result == "CLEAN"


def test_analyze_multiple_flagged_words_mixed_paths():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = _base_whitelist(force_flagged_lemmas=["مباشر"])
    tokens = [
        (0, "تحدث"), (1, "بشكل"), (2, "مباشر"),
        (3, "وكتب"), (4, "بشكل"), (5, "جميل"),
    ]
    flagged_indices = [2, 5]

    disambig_by_index = {
        2: {"pos": "noun", "pattern": "م12ا3", "lex": "مباشر"},
        5: {"pos": "adj", "pattern": "123ي", "lex": "جميل"},
    }

    def fake_disambiguate(tokens_arg):
        return [disambig_by_index.get(i) for i in range(len(tokens_arg))]

    def fake_force_flagged(lex, force_flagged_lemmas):
        return lex in force_flagged_lemmas

    def fake_nisba(info):
        return info["pattern"].endswith("ي") and info["pos"] == "adj"

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context", side_effect=fake_disambiguate), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.is_force_excluded", return_value=False), \
         patch("app.engine.rule_engine.is_force_flagged", side_effect=fake_force_flagged), \
         patch("app.engine.rule_engine.matches_nisba_pattern", side_effect=fake_nisba), \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=False), \
         patch("app.engine.rule_engine.build_match", side_effect=["MATCH_1", "MATCH_2"]), \
         patch("app.engine.rule_engine.clean_text"):

        result = analyze(RULES_PATH, WHITELIST_PATH, "تحدث بشكل مباشر وكتب بشكل جميل")

    assert result == ["MATCH_1", "MATCH_2"]
