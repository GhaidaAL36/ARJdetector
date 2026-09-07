import pytest
from app.engine.rule import (
    is_tam_trigger,
    is_in_waw_chain,
    is_whitelisted_lemma,
    is_phrase_whitelisted,
    describes_shakl,
    is_force_excluded,
)

""" whitelist check tests """


def test_is_whitelisted_lemma_returns_true_when_present():
    whitelisted_lemmas = ["دائر", "كروي", "مكعب"]

    assert is_whitelisted_lemma("كروي", whitelisted_lemmas) is True


def test_is_whitelisted_lemma_returns_false_when_absent():
    whitelisted_lemmas = ["دائر", "كروي", "مكعب"]

    assert is_whitelisted_lemma("رائع", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_empty_whitelist():
    assert is_whitelisted_lemma("دائر", []) is False


def test_is_whitelisted_lemma_matches_stripped_nisba_form():
    whitelisted_lemmas = ["دائر"]

    assert is_whitelisted_lemma("دائر", whitelisted_lemmas) is True
    assert is_whitelisted_lemma("دائري", whitelisted_lemmas) is False


def test_is_whitelisted_lemma_is_exact_match_not_substring():
    whitelisted_lemmas = ["دائر"]

    assert is_whitelisted_lemma("دا", whitelisted_lemmas) is False


def test_is_phrase_whitelisted_matches_two_word_phrase():
    tokens = list(enumerate(["بشكل", "شبه", "منحرف"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is True
    assert length == 2


def test_is_phrase_whitelisted_no_match_returns_false():
    tokens = list(enumerate(["بشكل", "كبير"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_single_word_not_confused_with_phrase():
    tokens = list(enumerate(["بشكل", "شبه", "كبير"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_not_enough_tokens_left():
    tokens = list(enumerate(["بشكل", "شبه"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_empty_whitelist():
    tokens = list(enumerate(["بشكل", "شبه", "منحرف"]))

    matched, length = is_phrase_whitelisted(tokens, 1, [])

    assert matched is False
    assert length == 1


def test_is_phrase_whitelisted_matches_at_nonzero_start_index():
    tokens = list(enumerate(["الخبز", "بشكل", "شبه", "منحرف", "لذيذ"]))
    whitelisted_phrases = ["شبه منحرف"]

    matched, length = is_phrase_whitelisted(tokens, 2, whitelisted_phrases)

    assert matched is True
    assert length == 2


def test_is_phrase_whitelisted_checks_multiple_candidate_phrases():
    tokens = list(enumerate(["بشكل", "شبه", "جزيرة"]))
    whitelisted_phrases = ["شبه منحرف", "شبه جزيرة"]

    matched, length = is_phrase_whitelisted(tokens, 1, whitelisted_phrases)

    assert matched is True
    assert length == 2


""" describes_shakl tests """


def _target(pos, prc0="0"):
    return {"pos": pos, "pattern": "", "lex": "", "prc0": prc0, "prc1": "0", "prc2": "0"}


def test_describes_shakl_true_for_adjective():
    assert describes_shakl(_target("adj")) is True


def test_describes_shakl_true_for_noun():
    """CAMeL returns noun for مباشر and عام after بشكل, and for يومي off the
    lemma يوم — demanding adj silently dropped all of them."""
    assert describes_shakl(_target("noun")) is True


def test_describes_shakl_true_for_proper_noun():
    """حسن is tagged noun_prop because it is also a name."""
    assert describes_shakl(_target("noun_prop")) is True


@pytest.mark.parametrize("pos", ["prep", "conj", "part_neg", "pron_rel", "verb", "punc"])
def test_describes_shakl_false_for_non_descriptors(pos):
    assert describes_shakl(_target(pos)) is False


def test_describes_shakl_false_when_target_is_definite():
    """«بشكل الهرم» is the genitive "in the shape of the pyramid" — the
    adverbial بشكل never takes a definite target."""
    assert describes_shakl(_target("noun", prc0="Al_det")) is False


def test_describes_shakl_definite_check_wins_over_pos():
    assert describes_shakl(_target("adj", prc0="Al_det")) is False


""" force_excluded tests """


def test_is_force_excluded_true_when_present():
    force_excluded_lemmas = ["واحد"]

    assert is_force_excluded("واحد", force_excluded_lemmas) is True


def test_is_force_excluded_false_when_absent():
    force_excluded_lemmas = ["واحد"]

    assert is_force_excluded("كبير", force_excluded_lemmas) is False


def test_is_force_excluded_empty_list():
    assert is_force_excluded("واحد", []) is False




""" is_tam_trigger tests """


def test_is_tam_trigger_true_for_the_verb():
    info = {"pos": "verb", "pattern": "1َ2َّ", "lex": "تم"}

    assert is_tam_trigger(info, "تم") is True


def test_is_tam_trigger_matches_prefixed_forms_through_the_lemma():
    """وتم / يتم / تمت all carry lex تم, so no prefix list is needed."""
    for pattern in ("و1َ2َّ", "ي1َ2ِّ", "1َ2َّت"):
        assert is_tam_trigger({"pos": "verb", "pattern": pattern, "lex": "تم"}, "تم")


def test_is_tam_trigger_false_for_nouns_ending_in_the_same_letters():
    """خاتم and مأتم end in تم but are nouns — a surface endswith test would
    flag them, which is why this checks lex and pos instead."""
    assert is_tam_trigger({"pos": "noun", "pattern": "1ا23", "lex": "خاتم"}, "تم") is False
    assert is_tam_trigger({"pos": "noun", "pattern": "م12ن", "lex": "مأتم"}, "تم") is False


def test_is_tam_trigger_false_for_proper_noun():
    info = {"pos": "noun_prop", "pattern": "1ا23", "lex": "حاتم"}

    assert is_tam_trigger(info, "تم") is False


def test_is_tam_trigger_false_when_lex_matches_but_pos_is_not_verb():
    info = {"pos": "noun", "pattern": "1َ2َّ", "lex": "تم"}

    assert is_tam_trigger(info, "تم") is False


""" is_in_waw_chain tests — bare series only (Ghaida, 2026-08-26) """


def _info(prc2="0", prc1="0", prc0="0"):
    return {"pos": "noun", "pattern": "", "lex": "", "prc1": prc1, "prc2": prc2,
            "prc0": prc0}


@pytest.mark.parametrize("proclitic", ["wa_part", "wa_conj", "wa_sub"])
def test_is_in_waw_chain_detects_every_waw_proclitic_value(proclitic):
    """CAMeL reads the same و three different ways — «والمراجعة» as wa_part but
    «وفتح» as wa_sub — so matching one value misses real chains."""
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "والمراجعة")]
    disambiguated = [_info(), _info(), _info(proclitic)]

    assert is_in_waw_chain(tokens, 1, disambiguated) is True


def test_is_in_waw_chain_detects_standalone_waw_token():
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "و"), (3, "المراجعة")]
    disambiguated = [_info(), _info(), _info(), _info()]

    assert is_in_waw_chain(tokens, 1, disambiguated) is True


def test_is_in_waw_chain_false_for_root_waw():
    """وصول starts with a و that is root material, not a conjunction — a
    spelling check would wrongly treat this as a chain. CAMeL reports "0"."""
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "وصول")]
    disambiguated = [_info(), _info(), _info("0")]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False


def test_is_in_waw_chain_false_when_next_word_is_plain():
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب")]
    disambiguated = [_info(), _info(), _info()]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False


def test_is_in_waw_chain_false_at_end_of_tokens():
    tokens = [(0, "تم"), (1, "إغلاق")]
    disambiguated = [_info(), _info()]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False


def test_is_in_waw_chain_true_even_when_the_head_governs_an_object():
    """§2.3 (2026-08-28) — «قام الفريق بفحص الموقع، وتقييم الأضرار» is فصيح even
    though each مصدر carries its own object. This previously asserted False."""
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب"), (3, "وفتح"), (4, "النافذة")]
    disambiguated = [_info(), _info(), _info(), _info("wa_conj"), _info()]

    assert is_in_waw_chain(tokens, 1, disambiguated) is True

def test_is_in_waw_chain_false_when_only_the_head_has_an_object():
    """«تم إغلاق الباب والنافذة» — asymmetric, so والنافذة is a second OBJECT,
    not a second مصدر. The construction collapses and must flag."""
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب"), (3, "والنافذة")]
    disambiguated = [_info(), _info(), _info(), _info("wa_conj")]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False

def test_is_in_waw_chain_does_not_stop_at_a_comma():
    """A comma between bare members does not end the chain."""
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "،"), (3, "والمراجعة")]
    disambiguated = [_info(), _info(), _info(), _info("wa_conj")]

    assert is_in_waw_chain(tokens, 1, disambiguated) is True


def test_is_in_waw_chain_stops_at_a_verb():
    """«تم إغلاق وذهب الرجل» — the و introduces a new clause with its own verb."""
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "وذهب"), (3, "الرجل")]
    disambiguated = [_info(), _info(), {**_info("wa_conj"), "pos": "verb"}, _info()]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False


def test_is_in_waw_chain_stops_at_sentence_end():
    tokens = [(0, "تم"), (1, "التدقيق"), (2, "."), (3, "والمراجعة")]
    disambiguated = [_info(), _info(), _info(), _info("wa_conj")]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False


def test_is_in_waw_chain_ignores_a_prepositional_phrase():
    """«تم إغلاق الباب وبشكل رائع كتب المقال» — «وبشكل» carries a preposition
    as well as the و, so it opens a phrase of its own rather than chaining."""
    tokens = [(0, "تم"), (1, "إغلاق"), (2, "الباب"), (3, "وبشكل"), (4, "رائع")]
    disambiguated = [
        _info(),
        _info(),
        _info(),
        _info(prc2="wa_conj", prc1="bi_prep"),
        _info(),
    ]

    assert is_in_waw_chain(tokens, 1, disambiguated) is False
