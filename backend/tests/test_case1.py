# -*- coding: utf-8 -*-
"""Coordinated مصدر series — قاعدة §2.3.

REVISED 2026-08-28. The objects test of 2026-08-26 is withdrawn: القاعدة's own
example «قام الفريق بفحص الموقع، وتقييم الأضرار، وإعداد التقرير النهائي» carries
a distinct object for each of its three masdars and is فصيح. So it is the series
itself that licenses قام بـ, not how the objects are distributed.

One function, shared with v2's تمّ masdar — same question, different start index.
"""
import csv
import io

import pytest

import goldsets

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_in_waw_chain, is_qam_trigger
from app.engine.rule_engine import analyze, qam_complement_index
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

SPEC = reader(rules_path)["qam"]
OVER = reader(whitelist_path)["qam"]


def qam_chain(sentence):
    tokens = preprocess(sentence)
    entries = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qam_trigger(tokens, index, entries, SPEC["trigger_lex"], OVER["mistagged_surfaces"]):
            complement = qam_complement_index(tokens, index, entries)
            if complement is None:
                return None
            return is_in_waw_chain(tokens, complement, entries)
    return None


@pytest.mark.parametrize(
    "sentence",
    [
        "قام الفريق بفحص الموقع، وتقييم الأضرار، وإعداد التقرير النهائي",
        "قامت الوزارة بحصر الأضرار وتعويض المتضررين وإعادة بناء المرافق",
        "قام الطالب بحل المسألة وكتابة الشرح",
        "قام الفريق بالتخطيط والتنفيذ",
        "قامت اللجنة بمراجعة الطلب ودراسة الحالة",
    ],
)
def test_real_any_masdar_series_is_silent(sentence):
    """§2.3 — bare, shared-object and distinct-object series alike."""
    assert qam_chain(sentence) is True
    assert analyze(rules_path, whitelist_path, sentence)["flagged"] is False


@goldsets.needs("labelled_set.csv")
def test_real_the_labelled_set_series_row_is_silent_again():
    rows = [r for r in goldsets.rows("labelled_set.csv")
            if "وتعويض المتضررين" in (r.get("sentence") or "")]

    assert [r["gold"] for r in rows] == ["SILENT"]
    assert analyze(rules_path, whitelist_path, rows[0]["sentence"])["flagged"] is False


@pytest.mark.parametrize(
    "sentence",
    ["قام الفريق بجمع وتحليل البيانات", "قامت الوزارة بإعداد ومراجعة التقرير"],
)
def test_real_masdars_sharing_one_object_flag(sentence):
    """Two مصادر, one مضاف إليه — «جمع وتحليل البيانات». عرنجي and a grammatical
    error: «جمع البياناتِ وحللها»."""
    assert analyze(rules_path, whitelist_path, sentence)["flagged"] is True


def test_real_a_single_masdar_is_not_a_series():
    assert qam_chain("قام الباحث بدراسة الظاهرة") is False


def test_real_a_verb_ends_the_series():
    """«وذهب الرجل» opens a new clause rather than continuing the list."""
    assert qam_chain("قام الفريق بدراسة الظاهرة وذهب الباحث") is False


""" v2's تمّ uses the same function """


@pytest.mark.parametrize(
    "sentence",
    ["تم التدقيق والمراجعة", "تم إغلاق الباب وفتح النافذة"],
)
def test_real_tam_parallel_series_passes(sentence):
    assert analyze(rules_path, whitelist_path, sentence) == {"flagged": False, "matches": []}


def test_real_tam_shared_object_series_now_flags():
    """«تم إغلاق وفتح الباب» — two مصادر sharing one مضاف إليه. القاعدة calls
    this عرنجي *and* a grammatical error; «أُغلق البابُ وفُتح» is the Arabic.
    Silenced between 2026-08-26 and 2026-08-28."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق وفتح الباب")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


""" the four و shapes — قاعدة, 2026-08-28 """


@pytest.mark.parametrize(
    "sentence, expected",
    [
        ("قام بالقراءة والتصحيح", False),
        ("قام بتصحيح الكتاب ومراجعة الاختبار", False),
        ("قام بقراءة الورقة والكتاب", True),
        ("قام بقراءة وتصحيح الكتاب", True),
    ],
)
def test_real_head_and_member_must_be_structurally_parallel(sentence, expected):
    """Both bare, or each with its own object -> a genuine مصدر series, فصيح.
    Asymmetric -> the و is coordinating objects, or the مصادر share one مضاف
    إليه — both collapse, so both flag."""
    assert analyze(rules_path, whitelist_path, sentence)["flagged"] is expected
