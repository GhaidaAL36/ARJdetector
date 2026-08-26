# -*- coding: utf-8 -*-
"""Case 1 / US-3 — one coordination rule, shared by v2's تمّ and v4's قام بـ."""
import csv
import io

import pytest

from app.config import rules_path, whitelist_path
from app.engine.analysis import get_pos_and_pattern_in_context
from app.engine.rule import is_in_waw_chain, is_qam_trigger
from app.engine.rule_engine import analyze, qam_complement_index
from app.rules.rule_loader import reader
from app.text.preprocessor import preprocess

LEXES = reader(rules_path)["qam_trigger_lex"]
MISTAGGED = reader(whitelist_path)["qam_mistagged_surfaces"]


def qam_chain(sentence):
    tokens = preprocess(sentence)
    entries = get_pos_and_pattern_in_context(tokens)
    for index, _ in tokens:
        if is_qam_trigger(tokens, index, entries, LEXES, MISTAGGED):
            complement = qam_complement_index(tokens, index, entries)
            if complement is None:
                return None
            return is_in_waw_chain(tokens, complement, entries)
    return None


""" v4 Case 1 — coordinated مصدر series stays silent """


@pytest.mark.parametrize(
    "sentence",
    [
        "قامت الوزارة بحصر الأضرار وتعويض المتضررين وإعادة بناء المرافق",
        "قام الفريق بجمع البيانات وتصنيفها",
        "قامت اللجنة بمراجعة الطلب ودراسة الحالة",
        "قام الباحث بتحليل العينات وتفسير النتائج",
    ],
)
def test_real_a_series_whose_members_carry_objects_is_not_suppressed(sentence):
    """RELABELLED 2026-08-26. Each مصدر governs its own object, so the whole
    construction collapses into direct verbs — «جمع الفريقُ البياناتِ وصنّفها» —
    and قام بـ is redundant. These previously asserted silence under القاعدة
    row 1's "the collapse target is plural" reasoning."""
    assert qam_chain(sentence) is False


@pytest.mark.parametrize(
    "sentence",
    ["قام الفريق بالتدقيق والمراجعة", "قامت اللجنة بالحصر والتعويض"],
)
def test_real_a_bare_series_is_suppressed(sentence):
    """Bare coordinated masdars carry no objects to redistribute — one unified
    functional action, so the periphrasis is doing real work."""
    assert qam_chain(sentence) is True


@pytest.mark.parametrize(
    "sentence",
    [
        "قام الباحث بدراسة الأسباب والنتائج",
        "قامت اللجنة بمراجعة التقارير والحسابات",
        "قام الفريق بتحليل العينات والبيانات",
        "قام الوزير بزيارة المصنع والمعرض",
    ],
)
def test_real_a_waw_inside_the_idafa_is_not_a_series(sentence):
    """The trap V4-5 named: «بدراسة الأسباب والنتائج» coordinates the OBJECT,
    so the collapse target is still singular and the sentence must stay
    flaggable. Only a coordinated series of مصدر heads suppresses."""
    assert qam_chain(sentence) is False


def test_real_the_labelled_set_has_no_case_one_row_left():
    """The single Case 1 row was relabelled to Case 4 on 2026-08-26 — its three
    masdars each carry an object, so it collapses and must flag."""
    rows = [
        r
        for r in csv.DictReader(io.open("doc/labelled_set.csv", encoding="utf-8-sig"))
        if r.get("case") == "Case 1"
    ]

    assert rows == []


""" v2 US-3 — the same function, and the same trap it used to fall into """


@pytest.mark.parametrize(
    "sentence", ["تم التدقيق والمراجعة", "تم إغلاق وفتح الباب"]
)
def test_real_tam_bare_series_still_passes(sentence):
    """Unchanged v2 behaviour — bare masdars, nothing to redistribute."""
    assert analyze(rules_path, whitelist_path, sentence) == {
        "flagged": False,
        "matches": [],
    }


@pytest.mark.parametrize(
    "sentence, phrase",
    [
        ("تم إغلاق الباب والنافذة", "تم إغلاق"),
        ("تم مراجعة التقارير والحسابات", "تم مراجعة"),
        ("تم تحليل العينات والبيانات", "تم تحليل"),
    ],
)
def test_real_tam_object_coordination_now_flags(sentence, phrase):
    """REGRESSION FIX. «أُغلق البابُ والنافذةُ» is the natural Arabic, so this is
    عرنجية — but the و-chain check used to silence it, because it read any
    و-noun as a coordinated masdar. A missed flag is invisible to the user."""
    result = analyze(rules_path, whitelist_path, sentence)

    assert [m["flagged_phrase"] for m in result["matches"]] == [phrase]


@pytest.mark.parametrize(
    "sentence",
    [
        "قام الباحث بدراسة أسباب ونتائج الظاهرة",
        "قامت اللجنة بمراجعة تقارير وحسابات الشركة",
        "قام الفريق بتحليل عينات وبيانات المشروع",
        "قام الوزير بزيارة مصانع ومعارض المدينة",
    ],
)
def test_real_an_indefinite_object_does_not_get_suppressed(sentence):
    """The all-indefinite branch: head, object and member agree, so nothing
    says which one the و joins. It must not suppress — these are عرنجية and a
    missed flag is invisible to the writer."""
    assert qam_chain(sentence) is False


@pytest.mark.parametrize(
    "sentence",
    [
        "قامت الوزارة بحصر أضرار وتعويض متضررين",
        "قام الباحث بتحليل عينات وتفسير نتائج",
    ],
)
def test_real_the_price_is_a_false_flag_on_an_all_indefinite_series(sentence):
    """The cost of the branch above, recorded rather than hidden: a genuine
    masdar series with an indefinite object is not suppressed either. A visible
    false flag is the trade the standing invariant asks for."""
    assert qam_chain(sentence) is False


def test_real_is_masdar_was_rejected_as_the_tiebreaker():
    """RULED OUT — do not re-try. is_masdar looked like it separated the
    ambiguous branch (4/4 on a first sample) but it calls these plural OBJECTS
    masdars, so they would be read as series members and silenced."""
    from app.engine.dictionary import is_masdar

    assert [w for w in ["أعمال", "أقوال", "تقارير", "طلبات", "أرقام"]
            if is_masdar(w) is True] == ["أعمال", "أقوال", "تقارير", "طلبات", "أرقام"]


""" known false negatives — Ghaida's correction, 2026-08-26 """


def test_real_coordinated_pair_with_own_objects_now_flags():
    """Was a known false negative, fixed 2026-08-26 by the objects test.
    «أُغلق البابُ وفُتحت النافذةُ» is clean Arabic, so تمّ is redundant."""
    result = analyze(rules_path, whitelist_path, "تم إغلاق الباب وفتح النافذة")

    assert [m["flagged_phrase"] for m in result["matches"]] == ["تم إغلاق"]


""" the three coordination shapes (Ghaida, 2026-08-26) """


@pytest.mark.parametrize(
    "sentence",
    ["قام الفريق بجمع وتصنيف البيانات", "قامت اللجنة بمراجعة ودراسة الطلب"],
)
def test_real_a_shared_object_is_suppressed_qam(sentence):
    """A SHARED object sits after the whole coordinated group, so the و is still
    adjacent to the head. Only a DISTINCT object per مصدر sits between them."""
    assert qam_chain(sentence) is True


@pytest.mark.parametrize(
    "sentence",
    ["تم إغلاق وفتح الباب", "تم إغلاق وفتح وتنظيف الباب", "تم مراجعة وتدقيق الحسابات"],
)
def test_real_a_shared_object_is_suppressed_tam(sentence):
    assert analyze(rules_path, whitelist_path, sentence) == {
        "flagged": False,
        "matches": [],
    }


def test_real_adjacency_is_what_separates_shared_from_distinct():
    """The same two masdars, one shared object vs one object each."""
    shared = analyze(rules_path, whitelist_path, "تم إغلاق وفتح الباب")
    distinct = analyze(rules_path, whitelist_path, "تم إغلاق الباب وفتح النافذة")

    assert shared["flagged"] is False
    assert [m["flagged_phrase"] for m in distinct["matches"]] == ["تم إغلاق"]
