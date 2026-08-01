from unittest.mock import Mock
from app.engine.rule_engine import find_flagged_words, analyze

""" find_flagged_words test """


def test_find_flagged_words():
    rules = {"trigger_word": "بشكل"}

    text = "تم بشكل سريع"

    result = find_flagged_words(rules, text)

    assert result == ["سريع"]


def test_trigger_word_at_end():
    rules = {"trigger_word": "بشكل"}

    text = "تم بشكل"

    result = find_flagged_words(rules, text)

    assert result == []


def test_no_trigger_word():
    rules = {"trigger_word": "بشكل"}

    text = "تم المشروع بنجاح"

    result = find_flagged_words(rules, text)

    assert result == []


def test_multiple_trigger_words():
    rules = {"trigger_word": "بشكل"}

    text = "تم بشكل سريع وبشكل واضح"

    result = find_flagged_words(rules, text)

    assert result == ["سريع", "واضح"]


def test_trigger_word_at_end_of_word():
    rules = {"trigger_word": "بشكل"}

    text = "تم وبشكل سريع"

    result = find_flagged_words(rules, text)

    assert result == ["سريع"]


""" analyze test """


def test_analyze_whitelisted_word(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["عام"],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["عام"]
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_analyze_word_starting_with_al(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["السريع"]
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_analyze_nisba_word(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["وطني"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["123ي"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: True
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_analyze_flagged_word(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }
    suggestions = {"سريع": "some suggestion"}

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else suggestions,
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["سريع"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["1ا23"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: False
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", lambda rules, pattern: True
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.build_match",
        lambda trigger_word, word, special_cases: {
            "flagged": True,
            "flagged_phrase": f"{trigger_word} {word}",
            "reason": None,
        },
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == [{"flagged": True, "flagged_phrase": "بشكل سريع", "reason": None}]


def test_analyze_non_flagged_pattern(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23", "12ي3"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["مثلث"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["م123"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: False
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", lambda rules, pattern: False
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_analyze_no_flagged_words(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23", "12ي3"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: []
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_whitelist_takes_priority_over_flagged_pattern(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["غاضب"],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["غاضب"]
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}


def test_analyze_multiple_flagged_words(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words",
        lambda rules, text: ["سريع", "غاضب"],
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["1ا23"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: False
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", lambda rules, pattern: True
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.build_match",
        lambda trigger_word, word, special_cases: {
            "flagged": True,
            "flagged_phrase": f"{trigger_word} {word}",
            "reason": None,
        },
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == [
        {"flagged": True, "flagged_phrase": "بشكل سريع", "reason": None},
        {"flagged": True, "flagged_phrase": "بشكل غاضب", "reason": None},
    ]


def test_analyze_passes_suggestions_to_build_match(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }
    suggestions = {"سريع": "احتمال بديل"}
    received = {}

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else suggestions,
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["سريع"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["1ا23"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: False
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", lambda rules, pattern: True
    )

    def fake_build_match(trigger_word, word, special_cases):
        received["special_cases"] = special_cases
        return {"flagged": True, "flagged_phrase": word, "reason": None}

    monkeypatch.setattr("app.engine.rule_engine.build_match", fake_build_match)

    analyze("anything.json", "anysuggestion.json", "anything")

    assert received["special_cases"] == suggestions


def test_analyze_nisba_takes_priority_over_matched_pattern(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["وطني"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["123ي"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: True
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", lambda rules, pattern: True
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    build_match_mock = Mock()
    monkeypatch.setattr("app.engine.rule_engine.build_match", build_match_mock)

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}
    build_match_mock.assert_not_called()


def test_analyze_mixed_words_each_take_different_branch(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["عام"],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words",
        lambda rules, text: ["عام", "السريع", "وطني", "غاضب"],
    )

    def fake_get_pattern(word):
        return {"وطني": ["123ي"], "غاضب": ["1ا23"]}[word]

    def fake_matches_nisba_pattern(pattern):
        return pattern == ["123ي"]

    def fake_matches_flagged_pattern(rules, pattern):
        return pattern == ["1ا23"]

    monkeypatch.setattr("app.engine.rule_engine.get_pattern", fake_get_pattern)
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", fake_matches_nisba_pattern
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", fake_matches_flagged_pattern
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.build_match",
        lambda trigger_word, word, special_cases: {
            "flagged": True,
            "flagged_phrase": f"{trigger_word} {word}",
            "reason": None,
        },
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == [{"flagged": True, "flagged_phrase": "بشكل غاضب", "reason": None}]


def test_analyze_al_check_runs_before_pattern_lookup(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["السريع"]
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    get_pattern_mock = Mock()
    matches_nisba_mock = Mock()
    matches_flagged_pattern_mock = Mock()
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", get_pattern_mock)
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", matches_nisba_mock
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_flagged_pattern", matches_flagged_pattern_mock
    )

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}
    get_pattern_mock.assert_not_called()
    matches_nisba_mock.assert_not_called()
    matches_flagged_pattern_mock.assert_not_called()


def test_analyze_whitelist_check_runs_before_al_check(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["السريع"],
    }

    monkeypatch.setattr(
        "app.engine.rule_engine.reader",
        lambda path: rules if path == "anything.json" else {},
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["السريع"]
    )
    monkeypatch.setattr(
        "app.engine.rule_engine.clean_text",
        lambda: {"flagged": False, "message": "clean text"},
    )

    get_pattern_mock = Mock()
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", get_pattern_mock)

    result = analyze("anything.json", "anysuggestion.json", "anything")

    assert result == {"flagged": False, "message": "clean text"}
    get_pattern_mock.assert_not_called()
