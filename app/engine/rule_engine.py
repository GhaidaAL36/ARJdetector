from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess


def next_word_check(path, text):
    rules = reader(path)
    tokens = preprocess(text)
    next_word = ""

    for index, word in tokens:
        if word.endswith(rules["trigger_word"]):
            if index + 1 < len(tokens):
                token = tokens[index + 1]
                next_word = token[1]
    return next_word

