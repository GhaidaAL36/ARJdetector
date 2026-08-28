from app.engine.tags import (
    ADJ,
    AL_DET,
    DESCRIPTOR_POS,
    NO_PROCLITIC,
    NOUN,
    NOUN_QUANT,
    PART_NEG,
    SENTENCE_END,
    VERB,
    WAW_PROCLITICS,
)


def describes_shakl(pos_pattern_info):
    if pos_pattern_info.get("prc0") == AL_DET:
        return False
    return pos_pattern_info["pos"] in DESCRIPTOR_POS


def is_tam_trigger(pos_pattern_info, trigger_lex):
    return (
        pos_pattern_info["lex"] == trigger_lex and pos_pattern_info["pos"] == VERB
    )


def is_qam_trigger(
    tokens,
    index,
    disambiguated,
    trigger_lexes,
    mistagged_surfaces=None,
):
    info = disambiguated[index]
    if info["lex"] in trigger_lexes and info["pos"] == VERB:
        return True
    return _is_negated_qam_mistag(tokens, index, disambiguated, mistagged_surfaces)


def _is_negated_qam_mistag(tokens, index, disambiguated, mistagged_surfaces):

    if not mistagged_surfaces or tokens[index][1] not in mistagged_surfaces:
        return False
    if index == 0:
        return False
    return disambiguated[index - 1]["pos"] == PART_NEG


def is_result_noun(disambiguated, complement_index, result_nouns):
    if complement_index is None or not result_nouns:
        return False
    return disambiguated[complement_index].get("lex") in result_nouns


def is_described_complement(
    tokens, disambiguated, complement_index, mistagged_adjectives=None
):
    after = complement_index + 1
    if after >= len(disambiguated):
        return False
    if disambiguated[after].get("pos") == ADJ:
        return True
    return tokens[after][1] in (mistagged_adjectives or ())


def is_emphatic_negation(
    tokens,
    trigger_index,
    complement_index,
    disambiguated,
    emphasis_lexes,
    negation_surfaces=None,
    emphasis_surfaces=None,
):
    if trigger_index == 0 or complement_index is None:
        return False

    previous = tokens[trigger_index - 1][1]
    negated = (
        disambiguated[trigger_index - 1].get("pos") == PART_NEG
        or previous in (negation_surfaces or ())
    )
    if not negated:
        return False

    complement = disambiguated[complement_index]
    if (
        complement.get("pos") == NOUN_QUANT
        and complement.get("lex") in emphasis_lexes
    ):
        return True

    surface = tokens[complement_index][1]
    return surface.lstrip("و")[1:] in (emphasis_surfaces or ())


def _waw_member_index(tokens, index, disambiguated):
    word = tokens[index][1]
    if word == "و":
        following = index + 1
        return following if following < len(disambiguated) else None

    info = disambiguated[index]
    if (
        info.get("prc2") in WAW_PROCLITICS
        and info.get("pos") == NOUN
        and info.get("prc1") in NO_PROCLITIC
    ):
        return index
    return None


def is_in_waw_chain(tokens, target_index, disambiguated):
    for index in range(target_index + 1, len(tokens)):
        word = tokens[index][1]
        info = disambiguated[index]

        if word in SENTENCE_END:
            return False
        if info.get("pos") == VERB:
            return False

        if _waw_member_index(tokens, index, disambiguated) is not None:
            return True

        if word.isalpha():
            return False

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


def get_qam_suggestion():
    return "يمكن استبدال «قام بـ» بالفعل المباشر"


def get_qam_explanation():
    return "فعل مساعد زائد"
