from app.engine.tags import (
    AL_DET,
    DESCRIPTOR_POS,
    NO_PROCLITIC,
    NOUN,
    NON_GENITIVE_POS,
    NOUN_QUANT,
    PART_NEG,
    PREP,
    PRONOUN_SUFFIXES,
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


def is_qabl_trigger(tokens, index, disambiguated, prep_lex, head_surface):
    if index + 1 >= len(tokens):
        return False
    info = disambiguated[index]
    if info["lex"] != prep_lex or info["pos"] != PREP:
        return False
    return _is_qabl_head(tokens[index + 1][1], head_surface)


def _is_qabl_head(word, head_surface, pronoun_suffixes=PRONOUN_SUFFIXES):
    if word == head_surface:
        return True
    return _carries_pronoun(word, head_surface, pronoun_suffixes)


def _carries_pronoun(word, head_surface, pronoun_suffixes=PRONOUN_SUFFIXES):
    if word == head_surface or not word.startswith(head_surface):
        return False
    return word[len(head_surface):] in pronoun_suffixes


def has_qabl_genitive(tokens, head_index, disambiguated, head_surface):
    if _carries_pronoun(tokens[head_index][1], head_surface):
        return True
    if head_index + 1 >= len(tokens):
        return False
    return disambiguated[head_index + 1]["pos"] not in NON_GENITIVE_POS


def is_result_noun(disambiguated, complement_index, result_nouns):
    if complement_index is None or not result_nouns:
        return False
    return disambiguated[complement_index].get("lex") in result_nouns


def is_duty_noun(disambiguated, head_index, duty_nouns):
    if head_index is None or not duty_nouns:
        return False
    return disambiguated[head_index].get("lex") in duty_nouns


def is_licensed_pair(disambiguated, head_index, licensed_pairs):
    if head_index is None or not licensed_pairs:
        return False
    licensed = licensed_pairs.get(disambiguated[head_index].get("lex"))
    if not licensed:
        return False
    following = head_index + 1
    if following >= len(disambiguated):
        return False
    return disambiguated[following].get("lex") in licensed


def complement_head_index(disambiguated, complement_index):
    if complement_index is None:
        return None
    nxt = complement_index + 1
    if disambiguated[complement_index].get("pos") == NOUN_QUANT and nxt < len(
        disambiguated
    ):
        return nxt
    return complement_index


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


def _first_alpha(tokens, disambiguated, start, stop):
    for index in range(start, stop):
        if tokens[index][1] in SENTENCE_END:
            return None
        if disambiguated[index].get("pos") == VERB:
            return None
        if tokens[index][1].isalpha():
            return index
    return None


def is_in_waw_chain(tokens, target_index, disambiguated):
    for index in range(target_index + 1, len(tokens)):
        word = tokens[index][1]
        if word in SENTENCE_END:
            return False
        if disambiguated[index].get("pos") == VERB:
            return False

        member = _waw_member_index(tokens, index, disambiguated)
        if member is None:
            continue

        head_has_object = _first_alpha(tokens, disambiguated, target_index + 1, index) is not None
        member_has_object = _first_alpha(
            tokens, disambiguated, member + 1, len(tokens)
        ) is not None
        return head_has_object == member_has_object

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


def get_qabl_suggestion():
    return "يمكن إسناد الفعل إلى فاعله مباشرة، أو حذف «من قبل»"


def get_qabl_explanation():
    return "فاعل مُقحَم على المبني للمجهول"
