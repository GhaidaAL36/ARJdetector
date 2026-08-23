AL_DET = "Al_det"
DESCRIPTOR_POS = frozenset({"adj", "noun", "noun_prop"})


def describes_shakl(pos_pattern_info):
    if pos_pattern_info.get("prc0") == AL_DET:
        return False
    return pos_pattern_info["pos"] in DESCRIPTOR_POS


def is_tam_trigger(pos_pattern_info, trigger_lex):
    return (
        pos_pattern_info["lex"] == trigger_lex and pos_pattern_info["pos"] == "verb"
    )


WAW_PROCLITICS = frozenset({"wa_part", "wa_conj", "wa_sub"})
SENTENCE_END = frozenset({".", "!", "?", "؟", "۔"})
NO_PROCLITIC = frozenset({"0", "na", ""})


def is_in_waw_chain(tokens, target_index, disambiguated):
    for index in range(target_index + 1, len(tokens)):
        word = tokens[index][1]
        info = disambiguated[index]

        if word in SENTENCE_END:
            return False
        if info.get("pos") == "verb":
            return False
        if word == "و":
            return True
        if (
            info.get("prc2") in WAW_PROCLITICS
            and info.get("pos") == "noun"
            and info.get("prc1") in NO_PROCLITIC
        ):
            return True

    return False


def is_force_intransitive_masdar(word, force_intransitive_masdars):
    if word in force_intransitive_masdars:
        return True
    if word.startswith("ال"):
        return word[2:] in force_intransitive_masdars
    return False


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


def is_force_excluded(lex, force_excluded_lemmas):
    return lex in force_excluded_lemmas


def get_suggestion():
    return "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية"


def get_explanation():
    FIXED_EXPLANATION = "حشو أسلوبي"
    return FIXED_EXPLANATION


def get_tam_suggestion():
    return "يمكن استبدال «تم» بفعل مبني للمجهول مباشرة"


def get_tam_explanation():
    return "مبني للمجهول مُعرَّب"
