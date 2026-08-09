from app.engine.match import build_match, clean_text


def test_build_match_returns_correct_shape():
    result = build_match("بشكل", "جميل")

    assert result["flagged"] is True
    assert result["flagged_phrase"] == "بشكل جميل"
    assert result["explanation"] == "حشو أسلوبي"
    assert result["suggestion"] == "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية"


def test_clean_text_returns_correct_shape():
    result = clean_text()

    assert result == {"flagged": False, "message": "clean text"}
