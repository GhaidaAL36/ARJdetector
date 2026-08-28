# -*- coding: utf-8 -*-
"""V4-8 — the v4 rule schema in data/.

Config holds **parameters, not answers**. Nothing here says which nouns are
light; that verdict comes from the collapse table, which is generated evidence
with its own provenance. These tests exist to make a drift toward a hand-written
noun list fail loudly rather than happen quietly.
"""
import pytest

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import find_qam_matches
from app.rules.rule_loader import reader

RULES = reader(rules_path)
WHITELIST = reader(whitelist_path)
SPEC = RULES["qam"]
OVERRIDES = WHITELIST["qam"]

#: Every key the v4 rule block is allowed to carry. Adding one means adding it
#: here first, which is the moment to ask whether it is a parameter or an answer.
ALLOWED_SPEC_KEYS = {
    "rule_id",
    "trigger_lex",
    "complement_proclitic",
    "complement_max_skip",
    "emphasis_lex",
}
ALLOWED_OVERRIDE_KEYS = {
    "mistagged_surfaces",
    "negation_surfaces",
    "emphasis_surfaces",
    "mistagged_adjectives",
    "result_nouns",
}

#: The Sprint Plan's cap. If it is reached, that is a finding about the
#: mechanism, not a reason to raise the cap.
RESULT_NOUN_CAP = 20

""" the shape """


def test_the_rule_block_declares_its_identity():
    assert SPEC["rule_id"] == "قام بـ"


def test_the_trigger_spec_is_lemma_plus_proclitic():
    """The trigger is a verb lemma; the complement is found by a proclitic."""
    assert SPEC["trigger_lex"] == ["قام", "قم", "قوم"]
    assert SPEC["complement_proclitic"] == "bi_prep"
    assert SPEC["complement_max_skip"] == 6


def test_the_rule_block_holds_only_parameters():
    """PARAMETERS, NOT ANSWERS. A new key here is the moment a noun list would
    sneak in, so an unrecognised one fails the build."""
    assert set(SPEC) == ALLOWED_SPEC_KEYS


def test_the_override_block_holds_only_the_known_lists():
    assert set(OVERRIDES) == ALLOWED_OVERRIDE_KEYS


""" no answers in data/ """


@pytest.mark.parametrize(
    "name", ["mistagged_surfaces", "negation_surfaces", "emphasis_surfaces"]
)
def test_every_camel_mistag_list_stays_bounded(name):
    """Each corrects one measured CAMeL mistag. If any grows, the mechanism is
    wrong — that is a finding, not a reason to add entries."""
    assert len(OVERRIDES[name]) <= 3, name


def test_the_result_noun_list_is_capped():
    """REOPENED 2026-08-27. Twelve mechanisms failed to separate event from
    result (see the decision record), so this became an explicit closed list.
    The cap is what keeps it closed."""
    assert len(OVERRIDES["result_nouns"]) <= RESULT_NOUN_CAP


def test_the_mistagged_adjective_list_stays_bounded():
    """Adjectives CAMeL returns as noun, which Case 5 would otherwise miss."""
    assert len(OVERRIDES["mistagged_adjectives"]) <= 10


def test_no_result_noun_would_silence_a_real_flag():
    """THE SAFETY PROPERTY, replacing V4-8's blanket 'no nouns in data/'.

    A word may be listed only if it never heads the complement of a gold FLAG
    row. This is what a bare 'no lists' rule was standing in for, and it is
    enforceable against the gold data instead of by prohibition."""
    import csv
    import io as _io

    from app.engine.analysis import get_pos_and_pattern_in_context
    from app.engine.rule_engine import qam_complement_index
    from app.engine.rule import is_qam_trigger
    from app.text.preprocessor import preprocess

    spec, over = RULES["qam"], WHITELIST["qam"]
    flagged_lexes = set()
    with _io.open("doc/labelled_set.csv", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("gold") != "FLAG":
                continue
            tokens = preprocess(row["sentence"])
            entries = get_pos_and_pattern_in_context(tokens)
            for index, _ in tokens:
                if is_qam_trigger(
                    tokens, index, entries, spec["trigger_lex"], over["mistagged_surfaces"]
                ):
                    complement = qam_complement_index(tokens, index, entries)
                    if complement is not None:
                        flagged_lexes.add(entries[complement]["lex"])
                    break

    overlap = sorted(set(over["result_nouns"]) & flagged_lexes)
    assert overlap == [], f"these entries would silence a gold FLAG row: {overlap}"


""" the tool must work with the overrides empty """


def test_the_rule_runs_with_every_override_list_empty():
    from app.engine.analysis import get_pos_and_pattern_in_context
    from app.text.preprocessor import preprocess

    tokens = preprocess("قام الباحث بدراسة الظاهرة")
    entries = get_pos_and_pattern_in_context(tokens)
    stripped = {"qam": {key: [] for key in ALLOWED_OVERRIDE_KEYS}}

    assert [m["flagged_phrase"] for _, m in find_qam_matches(
        RULES, stripped, tokens, entries)] == ["قام بدراسة"]


def test_the_rule_is_off_when_its_block_is_absent():
    """A v1/v2-only rules.json keeps working unchanged."""
    assert find_qam_matches({}, WHITELIST, [(0, "قام")], [{}]) == []
    assert find_qam_matches({"qam": {}}, WHITELIST, [(0, "قام")], [{}]) == []


""" v1 and v2 config is untouched """


def test_v1_and_v2_keys_still_read():
    assert RULES["trigger_word"] == "بشكل"
    assert RULES["tam_trigger_lex"] == "تم"
    assert len(WHITELIST["whitelisted_lemmas"]) == 22
    assert WHITELIST["force_intransitive_verbs"] == []


""" every rule declares its id the same way """


def test_all_three_rules_declare_a_rule_id():
    assert RULES["bshakl_rule_id"] == "بشكل"
    assert RULES["tam_rule_id"] == "تم"
    assert RULES["qam"]["rule_id"] == "قام بـ"


def test_the_rule_id_reaches_the_response():
    from app.engine.rule_engine import analyze

    result = analyze(rules_path, whitelist_path, "كتب المقال بشكل جميل وتم إغلاق الباب")

    assert [m["rule"] for m in result["matches"]] == ["بشكل", "تم"]


def test_a_config_without_rule_ids_falls_back_to_the_trigger():
    """v1/v2 configs predating this key keep working — the id defaults to the
    rule's own trigger, which is exactly what it was hardcoded to."""
    from unittest.mock import patch

    from app.engine.rule_engine import analyze

    legacy = {"trigger_word": "بشكل", "tam_trigger_lex": "تم"}
    with patch("app.engine.rule_engine.reader", side_effect=[legacy, WHITELIST]):
        result = analyze(rules_path, whitelist_path, "كتب المقال بشكل جميل")

    assert [m["rule"] for m in result["matches"]] == ["بشكل"]
