from app.engine.rule import (
    get_pattern,
    matches_flagged_pattern,
    matches_nisba_pattern,
    to_accusative_tanween,
    get_suggestion
)


""" get_pattern tests """


def test_get_pattern_faael():
    patterns = get_pattern("غاضب")

    assert "1ا23" in patterns


def test_get_pattern_faeel():
    patterns = get_pattern("كبير")

    assert "12ي3" in patterns


def test_non_flagged_pattern():
    patterns = get_pattern("مثلث")

    assert "م123" in patterns
    assert "1ا23" not in patterns
    assert "12ي3" not in patterns


def test_get_pattern_unrecognized_word():
    patterns = get_pattern("test")

    assert "FOREIGN" in patterns


def test_get_pattern_gibberish_word():
    patterns = get_pattern("هيسباكخب")

    assert [] == patterns


""" matches_flagged_pattern tests """


def test_all_patterns_are_flagged():
    rules = {"flagged_patterns": ["1ا23", "12ي3"]}

    patterns = ["1ا23", "12ي3"]

    assert matches_flagged_pattern(rules, patterns) is True


def test_one_pattern_is_flagged():
    rules = {"flagged_patterns": ["1ا23", "12ي3"]}

    patterns = ["م123", "1ا23"]

    assert matches_flagged_pattern(rules, patterns) is True


def test_no_pattern_is_flagged():
    rules = {"flagged_patterns": ["1ا23", "12ي3"]}

    patterns = ["م123"]

    assert matches_flagged_pattern(rules, patterns) is False


def test_unrecognized_word_pattern():
    rules = {"flagged_patterns": ["1ا23", "12ي3"]}

    pattern = []

    assert matches_flagged_pattern(rules, pattern) is False


""" matches_nisba_pattern tests """


def test_matches_nisba_pattern():
    patterns = ["م123", "123ي"]

    assert matches_nisba_pattern(patterns) is True


def test_no_nisba_pattern():
    patterns = ["1ا23", "م123"]

    assert matches_nisba_pattern(patterns) is False


def test_one_of_multiple_patterns_is_nisba():
    patterns = ["1ا23", "م123", "123ي"]

    assert matches_nisba_pattern(patterns) is True


def test_empty_pattern():
    patterns = []

    assert matches_nisba_pattern(patterns) is False


""" to_accusative_tanween tests """


def test_to_accusative_tanween_taa_marbuta():
    assert to_accusative_tanween("مدرسة") == "مدرسةً"


def test_to_accusative_tanween_alif_hamza():
    assert to_accusative_tanween("سماء") == "سماءً"


def test_alif_with_hamza_on_top():
    assert to_accusative_tanween("مبدأ") == "مبدأً"
    assert to_accusative_tanween("خطأ") == "خطأً"


def test_to_accusative_tanween_hamza():
    assert to_accusative_tanween("شيء") == "شيئاً"
    

def test_to_accusative_tanween_yaa():
    assert to_accusative_tanween("عربي") == "عربياً"
    

def test_to_accusative_tanween_default():
    assert to_accusative_tanween("كتاب") == "كتاباً"


""" get_suggestion tests """


def test_get_suggestion_special_case(monkeypatch):
    special_cases = {
        "خاص": "خصوصاً",
    }

    monkeypatch.setattr(
        "app.engine.rule.SPECIAL_CASES",
        special_cases
    )

    assert get_suggestion("خاص") == "خصوصاً"
    

def test_get_suggestion_regular_word(monkeypatch):
    monkeypatch.setattr(
        "app.engine.rule.SPECIAL_CASES",
        {}
    )

    monkeypatch.setattr(
        "app.engine.rule.to_accusative_tanween",
        lambda word: "EXPECTED"
    )

    assert get_suggestion("كتاب") == "EXPECTED"