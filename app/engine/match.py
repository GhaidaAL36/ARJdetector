from app.engine.rule import get_explanation, get_suggestion


def build_match(trigger_word, word):
    
    return {
        "flagged": True,
        "flagged_phrase": trigger_word + " " + word,
        "explanation": get_explanation(),
        "suggestion": get_suggestion(),
    }


def clean_text():
    return {"flagged": False, "message": "clean text"}
