from app.engine.rule import (
    is_whitelisted_lemma,
    is_phrase_whitelisted,
    matches_flagged_pattern,
    matches_nisba_pattern,
    is_force_flagged,
    is_force_excluded,
)

""" whitelist check tests """


def test_is_whitelisted_lemma_returns_true_when_present():
    whitelisted_lemmas = ["دائر", "كروي", "مكعب"]

    assert is_whitelisted_lemma("كروي", whitelisted_lemmas) is True


def test_is_whitelisted_lemma_returns_false_when_absent():
    whitelisted_lemmas = ["دائر", "كروي", "مكعب"]

    assert is_whitelisted_lemma("رائع", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_empty_whitelist():
    assert is_whitelisted_lemma("دائر", []) is False


def test_is_whitelisted_lemma_matches_stripped_nisba_form():
    whitelisted_lemmas = ["دائر"]

    assert is_whitelisted_lemma("دائر", whitelisted_lemmas) is True
    assert is_whitelisted_lemma("دائري", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_is_exact_match_not_substring():
    whitelisted_lemmas = ["دائر"]

    assert is_whitelisted_lemma("دا", whitelisted_lemmas) is False


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


""" force_flagged / force_excluded tests """


def test_is_force_flagged_true_when_present():
    force_flagged_lemmas = ["مباشر", "جميل", "واحد"]

    assert is_force_flagged("مباشر", force_flagged_lemmas) is True


def test_is_force_flagged_false_when_absent():
    force_flagged_lemmas = ["مباشر", "جميل", "واحد"]

    assert is_force_flagged("كبير", force_flagged_lemmas) is False


def test_is_force_flagged_empty_list():
    assert is_force_flagged("مباشر", []) is False


def test_is_force_excluded_true_when_present():
    force_excluded_lemmas = ["واحد"]

    assert is_force_excluded("واحد", force_excluded_lemmas) is True


def test_is_force_excluded_false_when_absent():
    force_excluded_lemmas = ["واحد"]

    assert is_force_excluded("كبير", force_excluded_lemmas) is False


def test_is_force_excluded_empty_list():
    assert is_force_excluded("واحد", []) is False


