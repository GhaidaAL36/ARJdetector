from app.engine.rule import (
    get_explanation,
    get_suggestion,
    get_tam_explanation,
    get_tam_suggestion,
)



def build_match(trigger_word, word, rule_id):
    return {
        "rule": rule_id,
        "flagged_phrase": trigger_word + " " + word,
        "explanation": get_explanation(),
        "suggestion": get_suggestion(),
    }


def build_tam_match(trigger_word, word, rule_id):
    return {
        "rule": rule_id,
        "flagged_phrase": trigger_word + " " + word,
        "explanation": get_tam_explanation(),
        "suggestion": get_tam_suggestion(),
    }


def build_response(matches):
    return {"flagged": bool(matches), "matches": matches}


def clean_text():
    return build_response([])
