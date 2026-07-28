from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess
from app.engine.rule import get_pattern, get_matches


def next_word_check(rules, text):
    tokens = preprocess(text)
    next_word = []

    for index, word in tokens:
        if word.endswith(rules["trigger_word"]):
            if index + 1 < len(tokens):
                token = tokens[index + 1]
                next_word.append(token[1])
    return next_word

def analyze(path, text):
    rules = reader(path)
    words = next_word_check(rules, text)
    result = []
    
    
    for word in words:
        pattern = get_pattern(word)
        is_match = get_matches(word, rules, pattern)

        if (is_match):
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

path = "data/rules.json"
text = "غضب المدير بشكل"
print(analyze(path, text))