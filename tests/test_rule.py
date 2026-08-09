from unittest.mock import patch, MagicMock
from app.engine.rule import (
    get_pos_and_pattern_in_context,
    is_whitelisted_lemma,
    is_phrase_whitelisted,
    matches_flagged_pattern,
    matches_nisba_pattern,
)

""" pos, pattern, lex check tests """


def make_fake_disambiguated_word(word, pos, pattern, lex):
    fake_entry = MagicMock()
    fake_entry.analyses = [
        MagicMock(analysis={"pos": pos, "pattern": pattern, "lex": lex})
    ]
    return fake_entry


def test_extracts_pos_pattern_lex_for_single_word():
    tokens = [(0, "مصنع")]
    fake_result = [make_fake_disambiguated_word("مصنع", "noun", "مَ1ْ2َ3ٍ", "مَصْنَع")]

    with patch("app.engine.rule._mle") as mock_mle:
        mock_mle.disambiguate.return_value = fake_result
        results = get_pos_and_pattern_in_context(tokens)

    assert results == [{"pos": "noun", "pattern": "م123", "lex": "مصنع"}]


def test_dediacritizes_pattern_and_lex():
    tokens = [(0, "مستمر")]
    fake_result = [
        make_fake_disambiguated_word("مستمر", "adj", "مُسْتَمِر", "مُسْتَمِر")
    ]

    with patch("app.engine.rule._mle") as mock_mle:
        mock_mle.disambiguate.return_value = fake_result
        results = get_pos_and_pattern_in_context(tokens)

    assert results[0]["pattern"] == "مستمر"
    assert results[0]["lex"] == "مستمر"


def test_preserves_order_across_multiple_words():
    tokens = [(0, "الجو"), (1, "جميل"), (2, "بشكل"), (3, "رائع")]
    fake_result = [
        make_fake_disambiguated_word("الجو", "noun", "ال123", "جو"),
        make_fake_disambiguated_word("جميل", "adj", "12ي3", "جميل"),
        make_fake_disambiguated_word("بشكل", "noun", "1234", "شكل"),
        make_fake_disambiguated_word("رائع", "adj", "فاعل", "رائع"),
    ]

    with patch("app.engine.rule._mle") as mock_mle:
        mock_mle.disambiguate.return_value = fake_result
        results = get_pos_and_pattern_in_context(tokens)

    assert len(results) == 4
    assert results[3]["pos"] == "adj"
    assert results[3]["lex"] == "رائع"


def test_picks_top_scored_analysis_when_multiple_exist():
    tokens = [(0, "مصنع")]
    fake_entry = MagicMock()
    fake_entry.analyses = [
        MagicMock(analysis={"pos": "noun", "pattern": "م123", "lex": "مصنع"}),
        MagicMock(analysis={"pos": "adj", "pattern": "م1ا23", "lex": "مصنوع"}),
    ]

    with patch("app.engine.rule._mle") as mock_mle:
        mock_mle.disambiguate.return_value = [fake_entry]
        results = get_pos_and_pattern_in_context(tokens)

    assert results[0]["pos"] == "noun"
    assert results[0]["lex"] == "مصنع"


def test_calls_disambiguate_with_words_only_not_index_pairs():
    tokens = [(0, "كتب"), (1, "بشكل")]

    with patch("app.engine.rule._mle") as mock_mle:
        mock_mle.disambiguate.return_value = [
            make_fake_disambiguated_word("كتب", "verb", "12َ3", "كتب"),
            make_fake_disambiguated_word("بشكل", "noun", "1234", "شكل"),
        ]
        get_pos_and_pattern_in_context(tokens)

    mock_mle.disambiguate.assert_called_once_with(["كتب", "بشكل"])


def test_real_disambiguation_مصنع_as_noun():
    tokens = list(enumerate(["مصنع", "الأدوية", "بشكل", "مستمر"]))

    results = get_pos_and_pattern_in_context(tokens)

    assert results[0]["pos"] == "noun"
    assert results[0]["lex"] == "مصنع"


def test_real_disambiguation_مستمر_as_adj():
    tokens = list(enumerate(["مصنع", "الأدوية", "بشكل", "مستمر"]))

    results = get_pos_and_pattern_in_context(tokens)

    assert results[3]["pos"] == "adj"


def test_real_disambiguation_returns_correct_length():
    tokens = list(enumerate(["الجو", "جميل", "بشكل", "رائع"]))

    results = get_pos_and_pattern_in_context(tokens)

    assert len(results) == 4


def test_real_pattern_and_lex_are_dediacritized():
    tokens = list(enumerate(["مصنع"]))

    results = get_pos_and_pattern_in_context(tokens)

    diacritics = "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652"
    assert not any(ch in diacritics for ch in results[0]["pattern"])
    assert not any(ch in diacritics for ch in results[0]["lex"])


""" whitelist check tests """


def test_is_whitelisted_lemma_returns_true_when_present():
    whitelisted_lemmas = ["دائري", "كروي", "مكعب"]

    assert is_whitelisted_lemma("كروي", whitelisted_lemmas) is True


def test_is_whitelisted_lemma_returns_false_when_absent():
    whitelisted_lemmas = ["دائري", "كروي", "مكعب"]

    assert is_whitelisted_lemma("رائع", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_empty_whitelist():
    assert is_whitelisted_lemma("دائري", []) is False


def test_is_whitelisted_lemma_is_exact_match_not_substring():
    whitelisted_lemmas = ["دائري"]

    assert is_whitelisted_lemma("دائر", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_case_sensitive_to_diacritics_if_present():
    whitelisted_lemmas = ["دائري"]

    assert is_whitelisted_lemma("دَائِري", whitelisted_lemmas) is False


def test_is_phrase_whitelisted_matches_two_word_phrase():
    tokens = list(enumerate(["بشكل", "شبه", "منحرف"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is True
    assert length == 2


def test_is_phrase_whitelisted_no_match_returns_false():
    tokens = list(enumerate(["بشكل", "كبير"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_single_word_not_confused_with_phrase():
    tokens = list(enumerate(["بشكل", "شبه", "كبير"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_not_enough_tokens_left():
    tokens = list(enumerate(["بشكل", "شبه"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_empty_whitelist():
    tokens = list(enumerate(["بشكل", "شبه", "منحرف"]))

    matched, length = is_phrase_whitelisted(tokens, 1, [])

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_matches_at_nonzero_start_index():
    tokens = list(enumerate(["الخبز", "بشكل", "شبه", "منحرف", "لذيذ"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 2, whitelisted_phrases)

    assert matched is True
    assert length == 2


def test_is_phrase_whitelisted_checks_multiple_candidate_phrases():
    tokens = list(enumerate(["بشكل", "شبه", "جزيرة"]))
    whitelisted_phrases = ["شبه منحرف", "شبه جزيرة"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is True
    assert length == 2


""" matches_flagged_pattern tests """


def test_matches_flagged_pattern_true_when_pattern_flagged_and_adj():
    rules = {"flagged_patterns": ["1ا23", "12ي3", "وا23"]}
    pos_pattern_info = {"pos": "adj", "pattern": "وا23", "lex": "واسع"}

    assert matches_flagged_pattern(rules, pos_pattern_info) is True


def test_matches_flagged_pattern_false_when_pattern_not_flagged():
    rules = {"flagged_patterns": ["1ا23", "12ي3"]}
    pos_pattern_info = {"pos": "adj", "pattern": "م123", "lex": "مصنع"}

    assert matches_flagged_pattern(rules, pos_pattern_info) is False


def test_matches_flagged_pattern_false_when_pattern_flagged_but_not_adj():
    rules = {"flagged_patterns": ["1ا23", "وا23"]}
    pos_pattern_info = {"pos": "noun", "pattern": "وا23", "lex": "واحد"}

    assert matches_flagged_pattern(rules, pos_pattern_info) is False


def test_matches_flagged_pattern_empty_flagged_patterns_list():
    rules = {"flagged_patterns": []}
    pos_pattern_info = {"pos": "adj", "pattern": "وا23", "lex": "واسع"}

    assert matches_flagged_pattern(rules, pos_pattern_info) is False


""" matches_nisba_pattern test """


def test_matches_nisba_pattern_true_for_رسمي():
    pos_pattern_info = {"pos": "adj", "pattern": "123ي", "lex": "رسمي"}

    assert matches_nisba_pattern(pos_pattern_info) is True


def test_matches_nisba_pattern_false_when_ends_with_ya_but_not_adj():
    pos_pattern_info = {"pos": "noun", "pattern": "12ي3", "lex": "كرسي"}

    assert matches_nisba_pattern(pos_pattern_info) is False


def test_matches_nisba_pattern_false_when_adj_but_does_not_end_with_ya():
    pos_pattern_info = {"pos": "adj", "pattern": "1ا23", "lex": "كبير"}

    assert matches_nisba_pattern(pos_pattern_info) is False


def test_matches_nisba_pattern_false_when_neither_condition_met():
    pos_pattern_info = {"pos": "noun", "pattern": "1ا23", "lex": "كتاب"}

    assert matches_nisba_pattern(pos_pattern_info) is False
