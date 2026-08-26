from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import (
    SENTENCE_END,
    describes_shakl,
    is_phrase_whitelisted,
    is_whitelisted_lemma,
    is_force_excluded,
    is_tam_trigger,
    is_in_waw_chain,
    is_force_intransitive_masdar,
)
from app.engine.derivation import derive_base_verb, is_trusted_derivation
from app.engine.dictionary import is_masdar, is_transitive_verb
from app.engine.match import build_match, build_tam_match, build_response

MAX_SKIP_TOKENS = 3
QAM_MAX_SKIP_TOKENS = 6
BI_PREP = "bi_prep"
ASIDE_DELIMITERS = {"(": ")", "[": "]", "«": "»", "-": "-", "—": "—", "،": "،"}
ASIDE_MAX_TOKENS = 8


def _closing_index(tokens, opener_index, closer):
    limit = min(opener_index + 1 + ASIDE_MAX_TOKENS, len(tokens))
    for index in range(opener_index + 1, limit):
        if tokens[index][1] == closer:
            return index
    return None


def next_target_index(tokens, index):
    position = index + 1
    skipped = 0

    while position < len(tokens) and skipped < MAX_SKIP_TOKENS:
        word = tokens[position][1]

        closer = ASIDE_DELIMITERS.get(word)
        if closer is not None:
            closing = _closing_index(tokens, position, closer)
            if closing is not None:
                position = closing + 1
                skipped += 1
                continue

        if word.isalpha():
            return position

        position += 1
        skipped += 1

    return None


def qam_complement_index(tokens, index, disambiguated, max_skip=QAM_MAX_SKIP_TOKENS):
    limit = min(index + 1 + max_skip, len(tokens))
    for position in range(index + 1, limit):
        if tokens[position][1] in SENTENCE_END:
            return None
        if disambiguated[position].get("prc1") == BI_PREP:
            return position

    return None


def find_bshakl_matches(rules, whitelist, tokens, disambiguated):
    trigger_word = rules["trigger_word"]
    matches = []

    for index, word in tokens:
        if not word.endswith(trigger_word):
            continue

        target_idx = next_target_index(tokens, index)
        if target_idx is None:
            continue

        is_phrase, _ = is_phrase_whitelisted(
            tokens, target_idx, whitelist["whitelisted_phrases"]
        )
        if is_phrase:
            continue

        info = disambiguated[target_idx]

        if is_whitelisted_lemma(info["lex"], whitelist["whitelisted_lemmas"]):
            continue

        if is_force_excluded(info["lex"], whitelist["force_excluded_lemmas"]):
            continue

        if not describes_shakl(info):
            continue

        matches.append((index, build_match(word, tokens[target_idx][1])))

    return matches


def masdar_target_index(tokens, index, disambiguated):
    fallback = None
    position = index + 1
    seen = 0

    while position < len(tokens) and seen < MAX_SKIP_TOKENS:
        word = tokens[position][1]

        if word in SENTENCE_END:
            break
        if disambiguated[position].get("pos") == "verb":
            break

        if word.isalpha():
            if disambiguated[position].get("pos") == "noun":
                return position
            if fallback is None:
                fallback = position
            seen += 1
        else:
            seen += 1

        position += 1

    return fallback


def find_tam_matches(rules, whitelist, tokens, disambiguated):
    trigger_lex = rules.get("tam_trigger_lex")
    if not trigger_lex:
        return []

    force_derived = whitelist.get("force_derived_verbs", {})
    force_intransitive = whitelist.get("force_intransitive_verbs", [])
    force_not_masdar = whitelist.get("force_not_masdar", [])
    force_intransitive_masdars = whitelist.get("force_intransitive_masdars", [])
    matches = []

    for index, word in tokens:
        if not is_tam_trigger(disambiguated[index], trigger_lex):
            continue

        target_idx = masdar_target_index(tokens, index, disambiguated)
        if target_idx is None:
            continue

        if is_in_waw_chain(tokens, target_idx, disambiguated):
            continue

        target = tokens[target_idx][1]

        if is_masdar(target, force_not_masdar) is False:
            continue

        if is_force_intransitive_masdar(target, force_intransitive_masdars):
            continue

        verb, status = derive_base_verb(target, force_derived)

        if not is_trusted_derivation(status):
            continue

        if is_transitive_verb(verb, force_intransitive):
            matches.append((index, build_tam_match(word, target)))

    return matches


def analyze(path, whitelist_path, text):
    rules = reader(path)
    whitelist = reader(whitelist_path)

    tokens = preprocess(text)
    if not tokens:
        return build_response([])

    has_trigger = any(word.endswith(rules["trigger_word"]) for _, word in tokens)
    if not has_trigger and not rules.get("tam_trigger_lex"):
        return build_response([])

    disambiguated = get_pos_and_pattern_in_context(tokens)

    found = find_bshakl_matches(rules, whitelist, tokens, disambiguated)
    found.extend(find_tam_matches(rules, whitelist, tokens, disambiguated))
    found.sort(key=lambda pair: pair[0])

    return build_response([match for _, match in found])
