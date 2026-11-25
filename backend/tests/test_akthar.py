# -*- coding: utf-8 -*-
"""v6.1 — GH002، «الأكثر/الأقلّ + صفة»: the fifth rule.

Arabic builds أفعل straight from the bare triliteral, so «الأكثر وضوحا» is
حشو for «الأوضح». But «الأكثر تطورا» is correct Arabic, because تطوّر is form V
and has no أفعل at all — so the rule turns on the **measure** of the described
word, which is a question about its shape and not about what it means.

Design C, ratified by Ghaida 2026-11-24 after four designs were scored over
2,608 corpus occurrences:

    trigger      lex أكثر/أقل + prc0 Al_det
    left check   a preceding على  ->  silent («على الأقل» = *at least*)
    target       the adjacent token
    pos gate     NON_DESCRIBED_POS deny-list; `verb` goes THROUGH
    measure      raw context pattern: I -> FLAG, II-X -> pass

Three of those steps are counter-intuitive and each one is a measured result,
so each has its own test below:

* the measure must be read from `raw_pattern`, never `pattern` — on a
  dediacritized pattern `classify_measure` falls through to "I" and the rule
  flags everything, which is his regex with extra steps;
* `verb` is NOT in the deny-list, because 76 occurrences of real تمييز are
  tagged verb in context (فقرا 58، فتكا 8);
* a preceding على is 38.5% of the trigger and 206 false flags.

No test in this file reads anything from `doc/`.
"""
import inspect

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import UNANALYSED
from app.engine.morphology import has_afal_form
from app.engine.rule import (
    is_akthar_blocked,
    is_akthar_trigger,
    is_described_target,
)
from app.engine.rule_engine import (
    analyze,
    find_akthar_matches,
    has_akthar_candidate,
)
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)
SPEC = RULES["akthar"]
RULE_ID = SPEC["rule_id"]
TRIGGER_LEXES = SPEC["trigger_lex"]
PROCLITIC = SPEC["trigger_proclitic"]
BLOCKING = SPEC["blocking_prev_lex"]


def info(pos="noun", lex="", prc0="0", raw_pattern="", pattern=""):
    return {
        "pos": pos,
        "lex": lex,
        "prc0": prc0,
        "prc1": "0",
        "prc2": "0",
        "pattern": pattern,
        "raw_pattern": raw_pattern,
    }


def akthar_matches(text):
    result = analyze(rules_path, whitelist_path, text)
    return [m for m in result["matches"] if m["rule"] == RULE_ID]


""" the trigger — lemma plus the article, never a surface list """


@pytest.mark.parametrize("lex", ["أكثر", "أقل"])
def test_the_trigger_fires_on_either_lemma_with_the_article(lex):
    assert is_akthar_trigger(info(lex=lex, prc0=PROCLITIC), TRIGGER_LEXES, PROCLITIC)


def test_a_bare_comparative_is_not_the_trigger():
    """«زار المدينة أكثر من مرة» — no article, so no تفضيل construction. This
    is why the test reads prc0 and not the surface spelling."""
    assert not is_akthar_trigger(info(lex="أكثر", prc0="0"), TRIGGER_LEXES, PROCLITIC)


def test_another_lemma_sharing_the_spelling_is_not_the_trigger():
    """«الأكثرية صوتت» reads lex=أكثرية, so the lemma test excludes it without
    anyone listing the word."""
    assert not is_akthar_trigger(
        info(lex="أكثرية", prc0=PROCLITIC), TRIGGER_LEXES, PROCLITIC
    )


def test_the_inert_entry_matches_no_akthar_predicate():
    assert is_akthar_trigger(UNANALYSED, TRIGGER_LEXES, PROCLITIC) is False
    assert has_afal_form(UNANALYSED["raw_pattern"], UNANALYSED["lex"]) is False


""" the left check — «على الأقل» is not this construction """


def test_a_preceding_ala_blocks_the_occurrence():
    disambiguated = [info(pos="prep", lex="على"), info(lex="أقل", prc0=PROCLITIC)]
    assert is_akthar_blocked(disambiguated, 1, BLOCKING)


def test_the_block_reads_the_lemma_so_it_covers_the_prefixed_forms():
    """على، وعلى، فعلى all return lex=على with pos=prep, the و/ف riding in
    prc2 — verified against CAMeL, which is why one key covers three forms."""
    disambiguated = [
        info(pos="prep", lex="على"),
        info(lex="أقل", prc0=PROCLITIC),
    ]
    assert is_akthar_blocked(disambiguated, 1, BLOCKING)


def test_a_trigger_at_the_start_of_the_text_is_not_blocked():
    assert not is_akthar_blocked([info(lex="أكثر", prc0=PROCLITIC)], 0, BLOCKING)


def test_ala_after_the_construction_does_not_block_it():
    """«الأكثر قدرة على الصمود» — the على is on the far side and irrelevant."""
    disambiguated = [
        info(lex="أكثر", prc0=PROCLITIC),
        info(lex="قدرة"),
        info(pos="prep", lex="على"),
    ]
    assert not is_akthar_blocked(disambiguated, 0, BLOCKING)


""" the pos gate — a DENY-list, and `verb` is deliberately outside it """


@pytest.mark.parametrize(
    "pos", ["prep", "conj", "conj_sub", "pron", "pron_rel", "part_neg", "digit", "adv"]
)
def test_a_function_word_cannot_be_the_described_target(pos):
    assert not is_described_target(info(pos=pos))


@pytest.mark.parametrize("pos", ["noun", "adj", "noun_prop", "verb"])
def test_a_descriptor_or_a_verb_tagged_token_reaches_the_measure_test(pos):
    """`verb` passes the gate on purpose: فقرا، فتكا، لفتا are real تمييز that
    CAMeL tags as verbs, and silencing them would be missed عرنجية."""
    assert is_described_target(info(pos=pos))


def test_an_unfamiliar_tag_reaches_the_measure_test():
    """THE POLARITY TEST. A tag CAMeL invents later must not silence the rule.
    An allow-list would default to silence, and silence is the error this
    project forbids."""
    assert is_described_target(info(pos="pos_camel_has_not_invented_yet"))


""" the measure — and it must come from the RAW pattern """


@pytest.mark.parametrize(
    "raw_pattern",
    ["1َ2ِ3ه", "1ِ2ْ3َةِ", "1ا2ِ3ِيَّةٍ", "1َ2ا3َةٍ"],
)
def test_measure_one_has_an_afal_form(raw_pattern):
    assert has_afal_form(raw_pattern)


@pytest.mark.parametrize(
    "raw_pattern",
    ["تَ1َوُّ3اً", "ٱِ1ْتِ2ا3اً", "ٱِسْتِ1ْ2ا3ا", "تَ1ْ2ِي3اً", "تَ1اوُ3ا"],
)
def test_measures_two_to_ten_have_none(raw_pattern):
    assert not has_afal_form(raw_pattern)


def test_the_forced_lemma_adds_a_flag_it_would_otherwise_miss():
    """أهمية is the مصدر of أهمَّ, so measure IV is CORRECT — but أهمّ is an
    attested تفضيل anyway. The list only ever adds a flag."""
    pattern = "أَ1َ2ِّيَّةً"
    assert not has_afal_form(pattern, "أهمية")
    assert has_afal_form(pattern, "أهمية", ["أهمية"])


def test_a_dediacritized_pattern_would_flag_everything():
    """THE GUARD FOR THE WHOLE RULE. `classify_measure` keys on kasra, sukun
    and shadda, and its fallback is "I". Feed it the dediacritized pattern and
    every form VIII/X word answers yes, i.e. the rule degrades to «flag
    anything after الأكثر» — silently, which is why this is a test."""
    assert not has_afal_form("ٱِ1ْتِ2ا3اً")
    assert has_afal_form("ا1ت2ا3")


""" the finder, with no CAMeL: absent config, and the overrides empty """


def test_the_finder_returns_nothing_when_the_block_is_absent():
    """A v1/v2/v4/v5-only config keeps working, exactly like its siblings."""
    assert find_akthar_matches({}, {}, [(0, "الأكثر"), (1, "وضوحا")], [], None) == []


def test_the_finder_works_with_the_forced_list_empty():
    """The rule must behave correctly with the override list absent, losing
    only أهمية. Required of every list in this repo."""
    tokens = [(0, "الأكثر"), (1, "أهمية")]
    disambiguated = [
        info(lex="أكثر", prc0=PROCLITIC),
        info(lex="أهمية", raw_pattern="أَ1َ2ِّيَّةً"),
    ]
    assert find_akthar_matches(RULES, {}, tokens, disambiguated) == []
    assert find_akthar_matches(RULES, WHITELIST, tokens, disambiguated)


""" end to end, real CAMeL """


@pytest.mark.parametrize(
    "text, phrase",
    [
        ("هذا هو الحل الأكثر فاعلية", "الأكثر فاعلية"),
        ("هو الأكثر رحمة بالناس", "الأكثر رحمة"),
        ("هي الأكثر جمالا بين أخواتها", "الأكثر جمالا"),
        ("فالأكثر حكمة أن نصمت", "فالأكثر حكمة"),
        ("يحتاج المشروع للأكثر خبرة من المهندسين", "للأكثر خبرة"),
    ],
)
def test_real_analyze_flags_a_measure_one_tamyiz(text, phrase):
    assert [m["flagged_phrase"] for m in akthar_matches(text)] == [phrase]


@pytest.mark.parametrize(
    "text",
    [
        "الأكثر تطورا من الأنظمة يحتاج صيانة",
        "المرض الأكثر انتشارا في المنطقة",
        "التطبيق الأكثر استخداما في العالم",
        "السهم الأكثر تداولا في السوق",
        "الشخصية الأكثر تأثيرا هذا العام",
        "المناطق الأكثر تضررا من الحرب",
        "المدينة الأقل تلوثا ليست هنا",
    ],
)
def test_real_analyze_passes_a_word_with_no_afal_form(text):
    """Measures II-X are correct Arabic and this is the precision the rule
    buys over a «الأكثر + any word» regex."""
    assert akthar_matches(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "قتل على الأقل خمسة أشخاص",
        "افترض أن ذلك صار على الأقل بعد تفجير المرفأ",
        "وعلى الأقل بينهم ثلاثة أطفال",
    ],
)
def test_real_analyze_passes_the_fixed_adverbial(text):
    """«على الأقل» is 1,008 of 2,608 corpus occurrences and 206 of the false
    flags before this check existed."""
    assert akthar_matches(text) == []


def test_real_analyze_flags_a_verb_tagged_tamyiz():
    """«الفئات الأكثر فقرا» → «الأفقر». CAMeL tags فقرا a verb in context, so
    a descriptor-only gate would silence it — 59 times in 300K."""
    assert [m["flagged_phrase"] for m in akthar_matches("الفئات الأكثر فقرا في البلاد")] == [
        "الأكثر فقرا"
    ]


def test_real_analyze_flags_the_forced_lemma():
    assert akthar_matches("وهذا هو الخيار الأكثر أهمية")


def test_real_analyze_passes_a_bare_comparative():
    assert akthar_matches("زار المدينة أكثر من مرة") == []


def test_real_analyze_passes_the_other_lemma():
    assert akthar_matches("الأكثرية صوتت لصالح القرار") == []


""" the response shape, same contract as the other four """


def test_the_match_carries_the_rule_id_from_data():
    found = akthar_matches("هذا هو الحل الأكثر فاعلية")
    assert found and found[0]["rule"] == RULE_ID


def test_the_spans_quote_the_flagged_text():
    text = "هذا هو الحل الأكثر فاعلية"
    found = akthar_matches(text)
    quoted = " ".join(text[s["start"] : s["end"]] for s in found[0]["spans"])
    assert quoted == found[0]["flagged_phrase"]


def test_trigger_and_target_merge_into_one_span():
    """They are adjacent by construction, so the highlight is one run."""
    found = akthar_matches("هذا هو الحل الأكثر فاعلية")
    assert len(found[0]["spans"]) == 1


""" the short-circuit """


def test_the_pre_check_is_wider_than_the_trigger():
    """A cheap pre-check that is narrower than the thing it gates fails
    invisibly, because the guarded code simply never runs. «الأكثرية» must
    reach the lemma test and be rejected there, not be dropped here."""
    for word in ["الأكثر", "الأقل", "فالأكثر", "للأكثر", "بالأكثر", "الأكثرية"]:
        assert has_akthar_candidate(RULES, [(0, word)]), word


def test_the_pre_check_says_no_on_ordinary_text():
    assert not has_akthar_candidate(RULES, [(0, "الجو"), (1, "جميل")])


def test_the_pre_check_says_no_when_the_block_is_absent():
    assert not has_akthar_candidate({}, [(0, "الأكثر")])


""" the strings """


def test_the_messages_take_no_input():
    from app.engine.rule import get_akthar_explanation, get_akthar_suggestion

    assert inspect.signature(get_akthar_suggestion).parameters == {}
    assert inspect.signature(get_akthar_explanation).parameters == {}
