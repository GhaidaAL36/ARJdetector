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
        "whitelisted_words": ["عام"]
    }
    
    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
    monkeypatch.setattr("app.engine.rule_engine.find_flagged_words", lambda rules, text: ["عام"])
    
    result = analyze("anything.json", "anything")
    
    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]
    
def test_analyze_word_starting_with_al(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": []
    }
    
    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
    monkeypatch.setattr("app.engine.rule_engine.find_flagged_words", lambda rules, text: ["السريع"])
    

    result = analyze("anything.json", "anything")

    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]

def test_analyze_nisba_word(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": []
    }

    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["وطني"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["123ي"])
    monkeypatch.setattr(
        "app.engine.rule_engine.matches_nisba_pattern", lambda pattern: True
    )

    result = analyze("anything.json", "anything")

    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]

def test_analyze_flagged_word(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": [],
    }

    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
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

    result = analyze("anything.json", "anything")

    assert result == [{"flagged": True, "flagged_phrase": "بشكل سريع", "reason": None}]

def test_analyze_non_flagged_pattern(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23", "12ي3"],
        "whitelisted_words": []
    }

    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
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

    result = analyze("anything.json", "anything")

    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]


def test_analyze_no_flagged_words(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23", "12ي3"],
        "whitelisted_words": []
    }

    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: []
    )

    result = analyze("anything.json", "anything")

    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]

def test_whitelist_takes_priority_over_flagged_pattern(monkeypatch):
    rules = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["غاضب"]
    }

    monkeypatch.setattr("app.engine.rule_engine.reader", lambda path: rules)
    monkeypatch.setattr(
        "app.engine.rule_engine.find_flagged_words", lambda rules, text: ["غاضب"]
    )
    monkeypatch.setattr("app.engine.rule_engine.get_pattern", lambda word: ["1ا23"])

    result = analyze("anything.json", "anything")

    assert result == [
        {
            "flagged": False,
            "message": "clean text"
        }
    ]
