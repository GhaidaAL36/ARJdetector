def build_match(trigger_word, target, rule_id, explanation, suggestion):
    return {
        "rule": rule_id,
        "flagged_phrase": trigger_word + " " + target,
        "explanation": explanation,
        "suggestion": suggestion,
    }


def build_response(matches):
    return {"flagged": bool(matches), "matches": matches}
