# -*- coding: utf-8 -*-
"""V5T-13 and V5T-14 — the labelled sets as a regression suite, end to end.

**These measure nothing.** The 64 rows of `v5_review_sample.csv` were used to
*choose* the mechanism and the 193 of `v5_clitics.csv` describe a limitation
that was accepted rather than fixed. Their job is to stop a later edit silently
un-deciding a settled case — which is why every row is its own test case, so a
failure names the sentence instead of moving a count.

They run through **`analyze()`**, not through the two predicates. The predicate
pair is already pinned by `test_qabl_genitive.py`; what is checked here is the
shipped behaviour, with the other three rules live alongside it.

**V5T-14 is the standing invariant**: no sentence labelled عرنجي may come back
silent. It is asserted over *every* labelled file present, and it skips rows
whose verdict column is still empty — so `v5_heldout.csv` joins it automatically
as Ghaida labels it, with no edit here.

NOTE: every test in this file reads CSVs from `doc/`, which are gitignored —
Ghaida's own labelled sentences. All access goes through `tests/goldsets.py`, so
a checkout without them SKIPS instead of failing.
"""
import pytest

from app.config import rules_path, whitelist_path
from app.engine.rule_engine import analyze
from app.rules.rule_loader import reader

import goldsets

QABL_RULE_ID = reader(rules_path)["qabl"]["rule_id"]

REVIEW = "v5_review_sample.csv"
CLITICS = "v5_clitics.csv"
HELDOUT = "v5_heldout.csv"
ALL_SETS = (REVIEW, CLITICS, HELDOUT)

#: Both label conventions in use: the first set says FLAG/SILENT, the later two
#: say عرنجي/فصيح. Anything else — including an empty cell — means "not labelled".
FLAG_WORDS = {"FLAG", "عرنجي"}
SILENT_WORDS = {"SILENT", "فصيح"}

PRONOUN_HEAD = "قبل"


def gold_of(row):
    """True/False for a labelled row, None for one still blank.

    One row of the clitic set has `حكمك` and `case` transposed at source, so
    both columns are consulted before giving up.
    """
    for column in ("حكمك", "case"):
        value = (row.get(column) or "").strip()
        if value in FLAG_WORDS:
            return True
        if value in SILENT_WORDS:
            return False
    return None


def is_clitic_row(row):
    surface = (row.get("qabl_surface") or "").strip()
    return bool(surface) and surface != PRONOUN_HEAD


_CACHE = {}


def flagged(sentence):
    """Does the shipped pipeline report a «من قبل» match for this sentence?"""
    if sentence not in _CACHE:
        result = analyze(rules_path, whitelist_path, sentence)
        _CACHE[sentence] = any(
            match["rule"] == QABL_RULE_ID for match in result["matches"]
        )
    return _CACHE[sentence]


def labelled(name):
    return [row for row in goldsets.rows(name) if gold_of(row) is not None]


def ident(row):
    return (row.get("n") or row.get("stratum") or "") + " " + row["sentence"][:40]


""" V5T-13 — the 64 review rows, one test each """

REVIEW_ROWS = labelled(REVIEW)


@goldsets.needs(REVIEW)
@pytest.mark.parametrize("row", REVIEW_ROWS, ids=[ident(r) for r in REVIEW_ROWS] or None)
def test_each_review_row_still_decides_the_way_it_did(row):
    """A clitic row labelled SILENT is a KNOWN false flag — the documented
    limitation, not a surprise. It is identified structurally rather than by
    listing three sentences: the clitic branch has no decision to make, so every
    such row flags by construction. `test_the_known_cost_is_exactly_three_rows`
    stops that class growing quietly."""
    expected = gold_of(row)
    if expected is False and is_clitic_row(row):
        expected = True
    assert flagged(row["sentence"]) is expected


@goldsets.needs(REVIEW)
def test_the_known_cost_is_exactly_three_rows():
    """61/64. If this number moves, something decided differently — in either
    direction — and the per-row tests above will say which sentence."""
    rows = labelled(REVIEW)
    assert len(rows) == 64
    wrong = [r for r in rows if flagged(r["sentence"]) is not gold_of(r)]
    assert len(wrong) == 3, [r["sentence"][:60] for r in wrong]
    assert all(is_clitic_row(r) for r in wrong), "a NON-clitic error is a new failure mode"


@goldsets.needs(REVIEW)
def test_no_bare_row_is_wrong_in_either_direction():
    """The bare branch — 54 of the 64 rows — is exactly right. That is the part
    the deny-list decides, and it has no known cost at all."""
    bare = [r for r in labelled(REVIEW) if not is_clitic_row(r)]
    assert len(bare) == 54
    assert all(flagged(r["sentence"]) is gold_of(r) for r in bare)


""" V5T-14 — the standing invariant, over every labelled set """


@pytest.mark.parametrize("name", ALL_SETS)
def test_nothing_labelled_عرنجي_is_ever_silenced(name):
    """THE INVARIANT. False flags are tolerated; a silent miss is not.

    Asserted over every labelled file that is checked out. A file still being
    labelled contributes only its finished rows, so `v5_heldout.csv` starts
    counting the moment Ghaida fills in a verdict — no edit needed here.
    """
    rows = [row for row in labelled(name) if gold_of(row) is True]
    if not rows:
        pytest.skip(f"doc/{name} has no labelled عرنجي rows yet")

    missed = [row["sentence"] for row in rows if not flagged(row["sentence"])]
    assert missed == [], f"{len(missed)} missed عرنجية in {name}: {missed[:3]}"


def test_the_invariant_covers_more_than_one_set():
    """A guard on the guard: if every gold file vanished, the parametrized test
    above would skip everywhere and pass in silence."""
    present = [name for name in ALL_SETS if labelled(name)]
    if not present:
        pytest.skip("no labelled sets checked out")
    assert len(present) >= 2, present


@goldsets.needs(CLITICS)
def test_every_clitic_row_labelled_عرنجي_flags():
    """The 145 Case 1 rows, end to end. The clitic branch cannot silence, so
    this is really a check that the TRIGGER reaches all of them through the
    whole pipeline — the sampler found them with its own scan."""
    rows = [r for r in labelled(CLITICS) if gold_of(r) is True]
    assert len(rows) == 145
    assert all(flagged(r["sentence"]) for r in rows)


""" V5T-17 — the held-out run, pinned

NOTE: reads doc/v5_heldout.csv, gitignored. 50 sentences drawn at random from
`ara_news_2020_1M` (seed 0) AFTER the mechanism was frozen, labelled by Ghaida
without seeing the tool's verdict or the pos columns it decides on. Unlike every
other set here, this one measures rather than regresses.
"""

HELDOUT_ROWS = labelled(HELDOUT)


@goldsets.needs(HELDOUT)
def test_the_held_out_run_scores_as_recorded():
    """47/50, ZERO missed عرنجية, 3 false flags — the number V5T-17 produced on
    its single run. It sits inside the development set's 61/64, which is the
    evidence that the mechanism was not fitted to those 64 rows.

    All three misses are the bare branch's known-mixed cases; the set drew no
    clitics, so it says nothing about that branch (see `v5_clitics.csv`).
    """
    rows = labelled(HELDOUT)
    assert len(rows) == 50

    missed = [r for r in rows if gold_of(r) and not flagged(r["sentence"])]
    false_flags = [r for r in rows if not gold_of(r) and flagged(r["sentence"])]

    assert missed == [], [r["sentence"][:60] for r in missed]
    assert len(false_flags) == 3, [r["sentence"][:60] for r in false_flags]
    assert len(rows) - len(false_flags) == 47


@goldsets.needs(HELDOUT)
def test_the_held_out_set_is_all_bare():
    """Pins the caveat rather than leaving it in prose: a random draw of 50 at
    1.65% clitic frequency contains none, so this file measures one branch."""
    assert not any(is_clitic_row(r) for r in labelled(HELDOUT))


@goldsets.needs(HELDOUT)
def test_every_held_out_عرنجي_row_is_caught():
    """41/41 recall on sentences the mechanism has never seen. n=41 bounds the
    miss rate below ~7% at 95%, which is what "zero missed" is worth here —
    a real result, not proof the invariant can never break."""
    rows = [r for r in labelled(HELDOUT) if gold_of(r) is True]
    assert len(rows) == 41
    assert all(flagged(r["sentence"]) for r in rows)
