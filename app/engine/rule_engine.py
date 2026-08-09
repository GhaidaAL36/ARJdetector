from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess
from app.engine.rule import (
    get_pos_and_pattern_in_context,
    matches_flagged_pattern,
    matches_nisba_pattern,
    is_phrase_whitelisted,
    is_whitelisted_lemma
)
from app.engine.match import build_match, clean_text


def find_flagged_words(rules, whitelist, text):
    tokens = preprocess(text)
    flagged_indices = []

    for index, word in tokens:
        if word.endswith(rules["trigger_word"]):
            if index + 1 >= len(tokens):
                continue
            
            next_word = tokens[index + 1][1]
            if not next_word.isalpha():
                continue

            is_phrase, _ = is_phrase_whitelisted(
                tokens, index + 1, whitelist["whitelisted_phrases"]
            )
            if is_phrase:
                continue

            flagged_indices.append(index + 1)

    return tokens, flagged_indices


def analyze(path, whitelist_path, text):
    rules = reader(path)
    whitelist = reader(whitelist_path)

    tokens, flagged_indices = find_flagged_words(rules, whitelist, text)
    result = []

    if flagged_indices:
        disambiguated = get_pos_and_pattern_in_context(tokens)

        for index in flagged_indices:
            word = tokens[index][1]
            pos_pattern_info = disambiguated[index]

            if is_whitelisted_lemma(pos_pattern_info["lex"], whitelist["whitelisted_lemmas"]):
                continue

            pattern = pos_pattern_info["pattern"]
            if pattern.startswith("ال"):
                pattern = pattern[2:]
            pos_pattern_info = {**pos_pattern_info, "pattern": pattern}

            is_nisba = matches_nisba_pattern(pos_pattern_info)
            matches_pattern = matches_flagged_pattern(rules, pos_pattern_info)

            if is_nisba or matches_pattern:
                result.append(build_match(rules["trigger_word"], word))

    if not result:
        result = clean_text()

    return result
