# -*- coding: utf-8 -*-
"""V5T-4 — the v5 rule schema in data/.

Same discipline as v4's `test_schema.py`: config holds **parameters, not
answers**. v5 has a sharper version of that rule, because it is the first rule
in this project that ships with **no override list at all** — no
`whitelist.json` block, no word list, nothing to tune. The tests below exist to
make a drift toward one fail loudly rather than happen quietly.

The two things v5 must never grow (see the v5 Sprint Plan, *Out of scope*):

* **a الجهة word list.** Case 3 is not detectable. It is ~0.5% of real
  occurrences, it is measured, and it is accepted. A list keyed on the word
  before «من قبل» (احترام، تقدير، مودة …) could never be finished, and it would
  hide the fact that the mechanism does not understand the distinction.
* **a clitic list in `data/`.** The nine pronoun suffixes are a *fact about
  Arabic*, not a setting. By v4's three-category table they live in Python
  beside their only consumer, exactly like `WEAK_LETTERS` and the form VIII
  infix table. Putting them here would advertise them as adjustable.

No test in this file reads anything from `doc/` — it is pure config, so it runs
on a bare checkout.
"""
import pytest

from app.config import rules_path, whitelist_path
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)
SPEC = RULES["qabl"]

#: Every key the v5 rule block is allowed to carry. Adding one means adding it
#: here first, which is the moment to ask whether it is a parameter or an answer.
ALLOWED_SPEC_KEYS = {
    "rule_id",
    "trigger_prep_lex",
    "trigger_head_surface",
}

#: The pronoun suffixes «من قبل» can carry. Named here only so the tests can
#: assert they are ABSENT from data/ — the real paradigm lives in Python.
PRONOUN_SUFFIXES = [
    "ه", "ها", "هما", "هم", "هن",
    "ك", "كما", "كم", "كن",
    "ي", "نا",
]


""" the shape """


def test_the_rule_block_declares_its_identity():
    assert SPEC["rule_id"] == "من قبل"


def test_the_trigger_spec_is_a_preposition_lemma_plus_a_head_surface():
    """The two halves are matched differently, and the key names say so.

    `من` is read from the analysis (`lex` + `pos == prep`), the same way v2's
    تمّ and v4's قام are. `قبل` cannot be: CAMeL reads `قبلك`/`قبلنا`/`قبلهم`/
    `قبلكم` as the verb `قَبِل` ("accepted") and `قبلي` as a preposition, so four
    of six persons never match a lemma test. The head is matched on **surface**
    — see V5T-6.
    """
    assert SPEC["trigger_prep_lex"] == "من"
    assert SPEC["trigger_head_surface"] == "قبل"


def test_the_rule_block_holds_only_parameters():
    """PARAMETERS, NOT ANSWERS. An unrecognised key fails the build, which is
    the moment a word list would otherwise sneak in."""
    assert set(SPEC) == ALLOWED_SPEC_KEYS


""" no answers in data/ — v5 ships with no override list at all """


def test_v5_has_no_override_block():
    """The distinguishing claim of v5. If this ever needs to change, that is a
    finding about the mechanism, not a routine edit."""
    assert "qabl" not in WHITELIST


def test_no_data_file_carries_a_jiha_word_list():
    """Case 3 is decided by nothing, deliberately. These are the words that sit
    before «من قبل» in the two gold Case 3 rows plus the obvious next
    candidates; none of them may appear in either data file."""
    blob = repr(RULES) + repr(WHITELIST)
    for word in ["احترام", "تقدير", "مودة", "ثقة", "خطأ", "تقصير", "أسلوب"]:
        assert word not in blob, f"{word} looks like the start of a الجهة list"


def test_the_clitic_paradigm_is_not_in_data():
    """A fact about Arabic, not a setting — it belongs in Python."""
    assert not any(
        key.endswith(("clitics", "suffixes", "pronouns")) for key in SPEC
    ), SPEC
    blob = repr(SPEC)
    attached = ["قبل" + suffix for suffix in PRONOUN_SUFFIXES]
    assert not any(form in blob for form in attached), SPEC


""" the earlier rules are untouched """


def test_v1_v2_and_v4_config_still_reads():
    """Adding the v5 block must not disturb anything already shipped."""
    assert RULES["trigger_word"] == "بشكل"
    assert RULES["tam_trigger_lex"] == "تم"
    assert RULES["qam"]["rule_id"] == "قام بـ"
    assert RULES["qam"]["trigger_lex"] == ["قام", "قم", "قوم"]
    assert set(WHITELIST["qam"]) == {
        "mistagged_surfaces",
        "result_nouns",
        "licensed_pairs",
        "duty_nouns",
    }


def test_every_rule_declares_a_rule_id():
    assert RULES["bshakl_rule_id"] == "بشكل"
    assert RULES["tam_rule_id"] == "تم"
    assert RULES["qam"]["rule_id"] == "قام بـ"
    assert RULES["qabl"]["rule_id"] == "من قبل"
