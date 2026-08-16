from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import (
    matches_flagged_pattern,
    matches_nisba_pattern,
    is_phrase_whitelisted,
    is_whitelisted_lemma,
    is_force_flagged,
    is_force_excluded,
)
from app.engine.match import build_match, clean_text

MAX_SKIP_TOKENS = 3


def find_flagged_words(rules, whitelist, text):
    tokens = preprocess(text)
    flagged_indices = []

    for index, word in tokens:
        if word.endswith(rules["trigger_word"]):
            target_idx = None
            for offset in range(1, MAX_SKIP_TOKENS + 1):
                candidate_idx = index + offset
                if candidate_idx >= len(tokens):
                    break
                if tokens[candidate_idx][1].isalpha():
                    target_idx = candidate_idx
                    break

            if target_idx is None:
                continue

            is_phrase, _ = is_phrase_whitelisted(
                tokens, target_idx, whitelist["whitelisted_phrases"]
            )
            if is_phrase:
                continue

            flagged_indices.append(target_idx)

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
            info = disambiguated[index]

            if is_whitelisted_lemma(info["lex"], whitelist["whitelisted_lemmas"]):
                continue

            if is_force_excluded(info["lex"], whitelist["force_excluded_lemmas"]):
                continue

            if is_force_flagged(info["lex"], whitelist["force_flagged_lemmas"]):
                result.append(build_match(rules["trigger_word"], word))
                continue

            pattern = info["pattern"]
            if pattern.startswith("ال"):
                pattern = pattern[2:]
            info = {**info, "pattern": pattern}

            if matches_nisba_pattern(info) or matches_flagged_pattern(rules, info):
                result.append(build_match(rules["trigger_word"], word))
    if not result:
        result = clean_text()

    return result
