import pytest
from unittest.mock import patch
from app.engine.rule_engine import find_flagged_words, analyze

""" find_flagged_words test """

def test_find_flagged_words_single_trigger():
    fake_tokens = [(0, "كتب"), (1, "المقال"), (2, "بشكل"), (3, "جميل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens) as mock_preprocess, \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "كتب المقال بشكل جميل")

    mock_preprocess.assert_called_once_with("كتب المقال بشكل جميل")
    assert tokens == fake_tokens
    assert flagged_indices == [3]


def test_find_flagged_words_waw_prefix_variant():
    fake_tokens = [(0, "تحسن"), (1, "الوضع"), (2, "وبشكل"), (3, "ملحوظ")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)):

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "تحسن الوضع وبشكل ملحوظ")

    assert flagged_indices == [3]


def test_find_flagged_words_fa_prefix_variant():
    fake_tokens = [(0, "تغير"), (1, "الأمر"), (2, "فبشكل"), (3, "مفاجئ")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)):

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "تغير الأمر فبشكل مفاجئ")

    assert flagged_indices == [3]


def test_find_flagged_words_multiple_triggers_in_one_text():
    fake_tokens = [
        (0, "الجو"), (1, "جميل"), (2, "بشكل"), (3, "رائع"),
        (4, "اليوم"), (5, "وبشكل"), (6, "كبير"),
    ]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "الجو جميل بشكل رائع اليوم وبشكل كبير"
        )

    assert flagged_indices == [3, 6]


def test_find_flagged_words_whitelisted_phrase_is_skipped():
    fake_tokens = [(0, "هذا"), (1, "الخبز"), (2, "بشكل"), (3, "شبه"), (4, "منحرف")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": ["شبه منحرف"]}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(True, 2)) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "هذا الخبز بشكل شبه منحرف"
        )

    mock_phrase.assert_called_once_with(fake_tokens, 3, ["شبه منحرف"])
    assert flagged_indices == []


def test_find_flagged_words_returns_full_tokens_even_when_nothing_flagged():
    fake_tokens = [(0, "هذا"), (1, "الخبز"), (2, "بشكل"), (3, "شبه"), (4, "منحرف")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": ["شبه منحرف"]}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(True, 2)):

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "هذا الخبز بشكل شبه منحرف"
        )

    assert tokens == fake_tokens


def test_find_flagged_words_trigger_is_last_word_no_crash():
    fake_tokens = [(0, "كتب"), (1, "المقال"), (2, "بشكل")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted") as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "كتب المقال بشكل")

    mock_phrase.assert_not_called()
    assert flagged_indices == []


def test_find_flagged_words_no_trigger_present():
    fake_tokens = [(0, "الجو"), (1, "جميل"), (2, "اليوم")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted") as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "الجو جميل اليوم")

    mock_phrase.assert_not_called()
    assert flagged_indices == []


def test_find_flagged_words_mixed_flagged_and_whitelisted_phrase():
    fake_tokens = [
        (0, "الخبز"), (1, "بشكل"), (2, "شبه"), (3, "منحرف"),
        (4, "والجو"), (5, "جميل"), (6, "بشكل"), (7, "رائع"),
    ]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": ["شبه منحرف"]}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", side_effect=[(True, 2), (False, 1)]) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "الخبز بشكل شبه منحرف والجو جميل بشكل رائع"
        )

    assert mock_phrase.call_count == 2
    assert flagged_indices == [7]


def test_find_flagged_words_calls_preprocess_with_original_text():
    fake_tokens = [(0, "كلمة")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens) as mock_preprocess, \
         patch("app.engine.rule_engine.is_phrase_whitelisted"):

        find_flagged_words(rules, whitelist, "نص عشوائي للاختبار")

    mock_preprocess.assert_called_once_with("نص عشوائي للاختبار")


def test_find_flagged_words_skips_punctuation_after_trigger():
    # وبشكل followed only by punctuation - must not be flagged
    fake_tokens = [
        (0, "الجو"), (1, "جميل"), (2, "بشكل"), (3, "كبير"),
        (4, "اليوم"), (5, "وبشكل"), (6, "."),
    ]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted", return_value=(False, 1)) as mock_phrase:

        tokens, flagged_indices = find_flagged_words(
            rules, whitelist, "الجو جميل بشكل كبير اليوم وبشكل."
        )

    # only index 3 (كبير) should be flagged - index 6 is punctuation, must be excluded
    assert flagged_indices == [3]
    # is_phrase_whitelisted should only be called once (for the real word), not for the period
    assert mock_phrase.call_count == 1


def test_find_flagged_words_skips_digit_after_trigger():
    fake_tokens = [(0, "زاد"), (1, "بشكل"), (2, "50")]
    rules = {"trigger_word": "بشكل"}
    whitelist = {"whitelisted_phrases": []}

    with patch("app.engine.rule_engine.preprocess", return_value=fake_tokens), \
         patch("app.engine.rule_engine.is_phrase_whitelisted") as mock_phrase:

        tokens, flagged_indices = find_flagged_words(rules, whitelist, "زاد بشكل 50")

    mock_phrase.assert_not_called()
    assert flagged_indices == []    


""" analyze test """

RULES_PATH = "fake/rules.json"
WHITELIST_PATH = "fake/whitelist.json"


def test_analyze_flags_word_via_nisba_pattern():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "جميل")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context",
               return_value=[None, None, {"pos": "adj", "pattern": "12ي3", "lex": "جميل"}]), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.matches_nisba_pattern", return_value=True), \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=False), \
         patch("app.engine.rule_engine.build_match", return_value="MATCH_RESULT") as mock_build, \
         patch("app.engine.rule_engine.clean_text") as mock_clean:

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل جميل")

    assert result == ["MATCH_RESULT"]
    mock_build.assert_called_once_with("بشكل", "جميل")
    mock_clean.assert_not_called()


def test_analyze_flags_word_via_flagged_pattern_not_nisba():
    rules = {"trigger_word": "بشكل", "flagged_patterns": ["وا23"]}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "واسع")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context",
               return_value=[None, None, {"pos": "adj", "pattern": "وا23", "lex": "واسع"}]), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.matches_nisba_pattern", return_value=False), \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=True), \
         patch("app.engine.rule_engine.build_match", return_value="MATCH_RESULT") as mock_build, \
         patch("app.engine.rule_engine.clean_text"):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل واسع")

    assert result == ["MATCH_RESULT"]
    mock_build.assert_called_once_with("بشكل", "واسع")


def test_analyze_skips_whitelisted_lemma():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = {"whitelisted_lemmas": ["دائري"], "whitelisted_phrases": []}
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "دائري")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context",
               return_value=[None, None, {"pos": "adj", "pattern": "12ي3", "lex": "دائري"}]), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=True) as mock_whitelist, \
         patch("app.engine.rule_engine.matches_nisba_pattern") as mock_nisba, \
         patch("app.engine.rule_engine.matches_flagged_pattern") as mock_flagged, \
         patch("app.engine.rule_engine.build_match") as mock_build, \
         patch("app.engine.rule_engine.clean_text", return_value="CLEAN"):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل دائري")

    mock_whitelist.assert_called_once_with("دائري", ["دائري"])
    mock_nisba.assert_not_called()
    mock_flagged.assert_not_called()
    mock_build.assert_not_called()
    assert result == "CLEAN"


def test_analyze_no_flagged_indices_returns_clean_text_without_calling_disambiguator():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [(0, "الجو"), (1, "جميل")]
    flagged_indices = []

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context") as mock_disambig, \
         patch("app.engine.rule_engine.clean_text", return_value="CLEAN"):

        result = analyze(RULES_PATH, WHITELIST_PATH, "الجو جميل")

    mock_disambig.assert_not_called()
    assert result == "CLEAN"


def test_analyze_strips_al_prefix_from_pattern_before_matching():
    rules = {"trigger_word": "بشكل", "flagged_patterns": ["12ي3"]}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "الكبير")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context",
               return_value=[None, None, {"pos": "adj", "pattern": "ال12ي3", "lex": "كبير"}]), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.matches_nisba_pattern", return_value=False) as mock_nisba, \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=True) as mock_flagged, \
         patch("app.engine.rule_engine.build_match", return_value="MATCH_RESULT"), \
         patch("app.engine.rule_engine.clean_text"):

        analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل الكبير")

    called_info = mock_flagged.call_args[0][1]
    assert called_info["pattern"] == "12ي3"

    called_info_nisba = mock_nisba.call_args[0][0]
    assert called_info_nisba["pattern"] == "12ي3"


def test_analyze_no_match_returns_clean_text():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [(0, "كتب"), (1, "بشكل"), (2, "شيء")]
    flagged_indices = [2]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context",
               return_value=[None, None, {"pos": "noun", "pattern": "123", "lex": "شيء"}]), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.matches_nisba_pattern", return_value=False), \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=False), \
         patch("app.engine.rule_engine.build_match") as mock_build, \
         patch("app.engine.rule_engine.clean_text", return_value="CLEAN"):

        result = analyze(RULES_PATH, WHITELIST_PATH, "كتب بشكل شيء")

    mock_build.assert_not_called()
    assert result == "CLEAN"


def test_analyze_multiple_flagged_words_both_match():
    rules = {"trigger_word": "بشكل", "flagged_patterns": []}
    whitelist = {"whitelisted_lemmas": [], "whitelisted_phrases": []}
    tokens = [
        (0, "الجو"), (1, "جميل"), (2, "بشكل"), (3, "رائع"),
        (4, "اليوم"), (5, "وبشكل"), (6, "كبير"),
    ]
    flagged_indices = [3, 6]

    disambig_by_index = {
        3: {"pos": "adj", "pattern": "فاعل", "lex": "رائع"},
        6: {"pos": "adj", "pattern": "12ي3", "lex": "كبير"},
    }

    def fake_disambiguate(tokens_arg):
        return [disambig_by_index.get(i) for i in range(len(tokens_arg))]

    with patch("app.engine.rule_engine.reader", side_effect=[rules, whitelist]), \
         patch("app.engine.rule_engine.find_flagged_words", return_value=(tokens, flagged_indices)), \
         patch("app.engine.rule_engine.get_pos_and_pattern_in_context", side_effect=fake_disambiguate), \
         patch("app.engine.rule_engine.is_whitelisted_lemma", return_value=False), \
         patch("app.engine.rule_engine.matches_nisba_pattern", return_value=True), \
         patch("app.engine.rule_engine.matches_flagged_pattern", return_value=False), \
         patch("app.engine.rule_engine.build_match", side_effect=["MATCH_1", "MATCH_2"]), \
         patch("app.engine.rule_engine.clean_text"):

        result = analyze(RULES_PATH, WHITELIST_PATH,
                          "الجو جميل بشكل رائع اليوم وبشكل كبير")

    assert result == ["MATCH_1", "MATCH_2"]
