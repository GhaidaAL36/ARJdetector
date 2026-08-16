from unittest.mock import patch, MagicMock
from app.engine.analysis import get_pos_and_pattern_in_context

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

    with patch("app.engine.analysis._mle") as mock_mle:
        mock_mle.disambiguate.return_value = fake_result
        results = get_pos_and_pattern_in_context(tokens)

    assert results == [{"pos": "noun", "pattern": "م123", "lex": "مصنع"}]


def test_dediacritizes_pattern_and_lex():
    tokens = [(0, "مستمر")]
    fake_result = [
        make_fake_disambiguated_word("مستمر", "adj", "مُسْتَمِر", "مُسْتَمِر")
    ]

    with patch("app.engine.analysis._mle") as mock_mle:
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

    with patch("app.engine.analysis._mle") as mock_mle:
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

    with patch("app.engine.analysis._mle") as mock_mle:
        mock_mle.disambiguate.return_value = [fake_entry]
        results = get_pos_and_pattern_in_context(tokens)

    assert results[0]["pos"] == "noun"
    assert results[0]["lex"] == "مصنع"


def test_calls_disambiguate_with_words_only_not_index_pairs():
    tokens = [(0, "كتب"), (1, "بشكل")]

    with patch("app.engine.analysis._mle") as mock_mle:
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


