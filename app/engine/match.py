from app.engine.rule import get_explanation, get_suggestion


def build_match(trigger_word, word, special_cases):
    
    return {
        "flagged": True,
        "flagged_phrase": trigger_word + " " + word,
        "explanation": get_explanation(),
        "suggestion": get_suggestion(word, special_cases),
    }


def clean_text():
    return {"flagged": False, "message": "clean text"}
