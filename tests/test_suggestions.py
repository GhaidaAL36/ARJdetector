# -*- coding: utf-8 -*-
"""V5T-19 — SETTLED: the suggestion is a fixed string, same as every other rule.

Ghaida's ruling, 2026-09-05: v5 does not generate a rewrite. It says what is
wrong and what kind of fix applies, and the writer writes it — the same shape
v1, v2 and v4 already ship.

**No code changed for this task**; `get_qabl_suggestion` was written that way and
this file pins the decision so a later "improvement" has to argue with a test.

What it rules out, so the options are on the record rather than rediscovered:

* **A generated rewrite.** «تمّت مراجعة الملف من قبل المشرف» → «راجع المشرفُ
  الملفَّ» needs the active verb plus correct case endings; → «رُوجِع الملفُّ»
  needs a passive *spelling*. Arramooz carries a `passive` boolean and no
  passive form, so neither is generatable today. This is the identical wall
  v2's US-4 still sits behind, and v5 sits behind it for the identical reason.
* **A different message for the clitic zone.** 51 of the tool's 54 false flags
  are «من قبل + ضمير», so a softer wording there was proposed at V5T-18. The
  ruling declines it: one rule, one message. A writer who can see *which* rule
  fired (V5T-12) has what they need to judge it.

The transferable point is that "say less, uniformly" was chosen over "say more,
inconsistently" — four rules that behave alike are easier to trust than four
that each have their own idea of helpfulness.
"""
import inspect

import pytest

from app.config import rules_path, whitelist_path
from app.engine import rule as rule_module
from app.engine.rule_engine import analyze
from app.rules.rule_loader import reader

RULES = reader(rules_path)

#: rule_id -> (suggestion fn, explanation fn, a sentence that fires it)
RULE_OUTPUT = {
    RULES["bshakl_rule_id"]: (
        rule_module.get_suggestion,
        rule_module.get_explanation,
        ["كتب المقال بشكل رائع", "تحدث الوزير بشكل واضح أمام الصحفيين"],
    ),
    RULES["tam_rule_id"]: (
        rule_module.get_tam_suggestion,
        rule_module.get_tam_explanation,
        ["تم إغلاق الباب", "تم توقيع الاتفاقية أمس"],
    ),
    RULES["qam"]["rule_id"]: (
        rule_module.get_qam_suggestion,
        rule_module.get_qam_explanation,
        ["قام الباحث بدراسة الظاهرة", "قامت اللجنة بمراجعة النتائج"],
    ),
    RULES["qabl"]["rule_id"]: (
        rule_module.get_qabl_suggestion,
        rule_module.get_qabl_explanation,
        [
            "تمت مراجعة الملف من قبل المشرف",
            "صدر القرار من قبل الوزارة",
            "تحظى بتقدير واحترام من قبلنا",
        ],
    ),
}


def matches_for(rule_id, text):
    result = analyze(rules_path, whitelist_path, text)
    return [m for m in result["matches"] if m["rule"] == rule_id]


""" the decision: fixed, not generated """


@pytest.mark.parametrize("rule_id", sorted(RULE_OUTPUT))
def test_the_text_takes_no_input_at_all(rule_id):
    """A function with no parameters CANNOT vary with the sentence. That is the
    decision expressed structurally — adding generation means changing this
    signature, which is exactly the moment to reopen V5T-19."""
    suggestion, explanation, _ = RULE_OUTPUT[rule_id]
    assert inspect.signature(suggestion).parameters == {}
    assert inspect.signature(explanation).parameters == {}


@pytest.mark.parametrize("rule_id", sorted(RULE_OUTPUT))
def test_every_match_of_a_rule_carries_the_same_text(rule_id):
    """Behavioural twin of the test above: different sentences, byte-identical
    output. For v5 the sentences span a bare agent phrase and a clitic one, so
    this also pins that the clitic zone gets no special message (V5T-18)."""
    suggestion, explanation, sentences = RULE_OUTPUT[rule_id]
    seen = set()
    for text in sentences:
        found = matches_for(rule_id, text)
        assert found, text
        for match in found:
            seen.add((match["explanation"], match["suggestion"]))
    assert seen == {(explanation(), suggestion())}, seen


""" and it is still a useful thing to say """


@pytest.mark.parametrize("rule_id", sorted(RULE_OUTPUT))
def test_each_rule_says_something_of_its_own(rule_id):
    suggestion, explanation, _ = RULE_OUTPUT[rule_id]
    assert suggestion().strip()
    assert explanation().strip()


def test_no_two_rules_share_a_message():
    """Four rules, four diagnoses. A shared string would make `rule` the only
    thing distinguishing them, which defeats the point of saying anything."""
    texts = [(s(), e()) for s, e, _ in RULE_OUTPUT.values()]
    assert len(set(texts)) == len(RULE_OUTPUT)
    assert len({e for _, e in texts}) == len(RULE_OUTPUT)


def test_the_qabl_message_names_the_construction_and_the_fix():
    """Not asserting the wording — asserting that it tells the writer which
    phrase to look at and what to do, which is what makes a fixed string
    sufficient instead of merely cheap."""
    match = matches_for(RULES["qabl"]["rule_id"], "تمت مراجعة الملف من قبل المشرف")[0]
    assert "من قبل" in match["suggestion"]
    assert match["flagged_phrase"] == "من قبل المشرف"
    assert match["explanation"] != match["suggestion"]
