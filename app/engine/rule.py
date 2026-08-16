def matches_flagged_pattern(rules, pos_pattern_info):
    return (
        pos_pattern_info["pattern"] in rules["flagged_patterns"]
        and pos_pattern_info["pos"] == "adj"
    )


def matches_nisba_pattern(pos_pattern_info):
    return (
        pos_pattern_info["pattern"].endswith("ي") and pos_pattern_info["pos"] == "adj"
    )


def is_whitelisted_lemma(lemma, whitelisted_lemmas):
    return lemma in whitelisted_lemmas


def is_phrase_whitelisted(tokens, start_index, whitelisted_phrases):
    for phrase in whitelisted_phrases:
        phrase_words = phrase.split()
        n = len(phrase_words)
        candidate = [w for _, w in tokens[start_index : start_index + n]]
        if candidate == phrase_words:
            return True, n
    return False, 1


def is_force_flagged(lex, force_flagged_lemmas):
    return lex in force_flagged_lemmas


def is_force_excluded(lex, force_excluded_lemmas):
    return lex in force_excluded_lemmas


def get_suggestion():
    return "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية"


def get_explanation():
    FIXED_EXPLANATION = "حشو أسلوبي"
    return FIXED_EXPLANATION
