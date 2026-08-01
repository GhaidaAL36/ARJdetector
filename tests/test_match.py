from unittest.mock import Mock

from app.engine.match import build_match, clean_text


def test_build_match_happy_path(monkeypatch):
    trigger_word = "بشكل"
    word = "سريع"
    special_cases = {"سريع": "بديل مقترح"}

    get_explanation_mock = Mock(return_value="EXPLANATION_SENTINEL")
    get_suggestion_mock = Mock(return_value="SUGGESTION_SENTINEL")
    monkeypatch.setattr("app.engine.match.get_explanation", get_explanation_mock)
    monkeypatch.setattr("app.engine.match.get_suggestion", get_suggestion_mock)

    result = build_match(trigger_word, word, special_cases)

    assert result == {
        "flagged": True,
        "flagged_phrase": "بشكل سريع",
        "explanation": "EXPLANATION_SENTINEL",
        "suggestion": "SUGGESTION_SENTINEL",
    }
    get_suggestion_mock.assert_called_once_with(word, special_cases)
    assert set(result.keys()) == {
        "flagged",
        "flagged_phrase",
        "explanation",
        "suggestion",
    }


def test_build_match_forwards_special_cases_unchanged(monkeypatch):
    trigger_word = "بشكل"
    word = "سريع"
    special_cases = {"سريع": "بديل مقترح"}
    received = {}

    def fake_get_suggestion(word, special_cases):
        received["word"] = word
        received["special_cases"] = special_cases
        return "SUGGESTION_SENTINEL"

    monkeypatch.setattr(
        "app.engine.match.get_explanation", lambda: "EXPLANATION_SENTINEL"
    )
    monkeypatch.setattr("app.engine.match.get_suggestion", fake_get_suggestion)

    build_match(trigger_word, word, special_cases)

    assert received["special_cases"] is special_cases
    assert received["word"] == word


def test_clean_text_returns_expected_dict():
    assert clean_text() == {"flagged": False, "message": "clean text"}