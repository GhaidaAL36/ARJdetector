from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess
from app.engine.rule import get_pattern, matches_flagged_pattern, matches_nisba_pattern


def find_flagged_words(rules, text):
    tokens = preprocess(text)
    next_words = []

    for index, word in tokens:
        if word.endswith(rules["trigger_word"]):
            if index + 1 < len(tokens):
                token = tokens[index + 1]
                next_words.append(token[1])
    return next_words

def analyze(path, text):
    rules = reader(path)
    words = find_flagged_words(rules, text)
    result = []
    
    for word in words:
        if word in rules["whitelisted_words"]:
            continue
        
        pattern = get_pattern(word)
        is_nisba = matches_nisba_pattern(pattern)
        matches_pattern = matches_flagged_pattern(rules, pattern)
        
        if (is_nisba):
            continue

        if (matches_pattern):
            result.append({
                "flagged": True,
                "flagged_phrase": rules["trigger_word"] + " " + word,
                "reason": None  
            })
      
    if not result:     
        result.append({
            "flagged": False,
            "message": "clean text"
        })
        
    return result
