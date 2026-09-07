def spans_for(token_spans, indices):
    if token_spans is None:
        return []

    merged = []
    for index in sorted(indices):
        start, end = token_spans[index]
        if merged and index == merged[-1][2] + 1:
            merged[-1] = (merged[-1][0], end, index)
        else:
            merged.append((start, end, index))

    return [{"start": start, "end": end} for start, end, _ in merged]


def build_match(trigger_word, target, rule_id, explanation, suggestion, spans):
    return {
        "rule": rule_id,
        "flagged_phrase": trigger_word + " " + target,
        "explanation": explanation,
        "suggestion": suggestion,
        "spans": spans,
    }


def build_response(matches):
    return {"flagged": bool(matches), "matches": matches}
