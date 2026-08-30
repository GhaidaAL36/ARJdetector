from app.engine.match import build_match, build_response
from app.engine.rule import (
    get_explanation,
    get_suggestion,
    get_tam_explanation,
    get_tam_suggestion,
)


def bshakl(word, target, rule_id="بشكل"):
    return build_match(word, target, rule_id, get_explanation(), get_suggestion())


def tam(word, target, rule_id="تم"):
    return build_match(word, target, rule_id, get_tam_explanation(), get_tam_suggestion())


def test_build_match_returns_correct_shape():
    result = bshakl("بشكل", "جميل")

    assert result["rule"] == "بشكل"
    assert result["flagged_phrase"] == "بشكل جميل"
    assert result["explanation"] == "حشو أسلوبي"
    assert result["suggestion"] == "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية"


def test_build_tam_match_returns_correct_shape():
    result = tam("تم", "استلام")

    assert result["rule"] == "تم"
    assert result["flagged_phrase"] == "تم استلام"
    assert result["explanation"] == "مبني للمجهول مُعرَّب"


def test_build_tam_match_carries_its_own_explanation():
    """The تمّ rule is a different problem from بشكل and must not reuse its
    wording."""
    assert tam("تم", "استلام")["explanation"] != bshakl(
        "بشكل", "جميل"
    )["explanation"]



def test_build_response_wraps_matches():
    matches = [{"rule": "تم", "flagged_phrase": "تم إغلاق"}]

    assert build_response(matches) == {"flagged": True, "matches": matches}


def test_build_response_shape_is_the_same_when_empty():
    """One shape for every reply — callers must not branch on the type."""
    assert set(build_response([])) == set(build_response([{"a": 1}]))


def test_the_rule_id_comes_from_the_caller_not_a_constant():
    """rule_id is config now — all three rules declare it the same way, and
    V4-15 surfaces it in the API response."""
    assert bshakl("بشكل", "جميل", "X")["rule"] == "X"
    assert tam("تم", "استلام", "Y")["rule"] == "Y"
