# -*- coding: utf-8 -*-
"""Character offsets for the flagged phrases.

The pipeline works on dediacritized tokens, so nothing in it knows where a
match sits in the text the user actually typed. `align_tokens` recovers that,
and `spans_for` turns the token indices a rule already has into the spans the
response carries.
"""
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.dediac import dediac_ar

from app.config import rules_path, whitelist_path
from app.engine.match import spans_for
from app.engine.rule_engine import analyze
from app.text.preprocessor import align_tokens, preprocess

SAMPLES = [
    "تم إطلاق المنصة الجديدة بشكل رسمي",
    "تمّ إطلاقُ المنصّةِ الجديدةِ بشكلٍ رسميّ",
    "قام الباحث المتخصص في علم الاجتماع بدراسة الظاهرة",
    "النص، بشكل - ولله الحمد - كبير (جدا) «هنا»",
    "text مع english و 123 و emoji 🙂 هنا",
    "تم  إطلاق\tالمنصة\nبشكل رسمي",
    "ٱكتشاف الأمر تم بشكل رسمي",
]


# --- the two CAMeL properties align_tokens is built on ------------------------
# Both were measured before the function was written. They are asserted here so
# a CAMeL upgrade that breaks either one fails a test, rather than silently
# shifting every highlight in the app.

def test_dediac_only_ever_deletes():
    for text in SAMPLES:
        clean = dediac_ar(text)
        walker = iter(text)
        assert all(character in walker for character in clean), text


def test_the_tokenizer_preserves_characters():
    for text in SAMPLES:
        clean = dediac_ar(text)
        joined = "".join(simple_word_tokenize(clean))
        assert joined == "".join(clean.split()), text


# --- align_tokens -------------------------------------------------------------

def test_every_span_quotes_its_own_token():
    for text in SAMPLES:
        tokens = preprocess(text)
        spans = align_tokens(text, tokens)
        assert len(spans) == len(tokens)
        for (_, token), (start, end) in zip(tokens, spans):
            assert dediac_ar(text[start:end]) == token, (text, token)


def test_spans_do_not_overlap_and_move_forward():
    for text in SAMPLES:
        spans = align_tokens(text, preprocess(text))
        for (_, previous_end), (next_start, _) in zip(spans, spans[1:]):
            assert previous_end <= next_start, text


def test_offsets_are_into_the_original_not_the_dediacritized_text():
    text = "تمّ إطلاقُ المنصّةِ"
    spans = align_tokens(text, preprocess(text))
    # dediac drops 4 marks here, so the third token starts 3 characters later
    # than it would in the dediacritized string.
    assert text[spans[0][0]:spans[0][1]] == "تمّ"
    assert text[spans[1][0]:spans[1][1]] == "إطلاقُ"
    assert text[spans[2][0]:spans[2][1]] == "المنصّةِ"


def test_a_span_covers_the_diacritics_hanging_off_its_token():
    text = "تمّ الأمر"
    start, end = align_tokens(text, preprocess(text))[0]
    # the shadda is not in the token, but it is part of the word on screen
    assert text[start:end] == "تمّ"


def test_repeated_phrases_get_distinct_spans():
    text = "بشكل رسمي ثم بشكل رسمي"
    spans = align_tokens(text, preprocess(text))
    assert spans[0] != spans[3]
    assert text[spans[3][0]:spans[3][1]] == "بشكل"


# --- spans_for ----------------------------------------------------------------

def test_adjacent_tokens_merge_into_one_span():
    token_spans = [(0, 2), (3, 8)]
    assert spans_for(token_spans, [0, 1]) == [{"start": 0, "end": 8}]


def test_separated_tokens_stay_separate():
    token_spans = [(0, 3), (4, 10), (11, 18)]
    assert spans_for(token_spans, [0, 2]) == [
        {"start": 0, "end": 3},
        {"start": 11, "end": 18},
    ]


def test_three_adjacent_tokens_merge_into_one_span():
    token_spans = [(0, 2), (3, 7), (8, 14)]
    assert spans_for(token_spans, [0, 1, 2]) == [{"start": 0, "end": 14}]


def test_indices_are_sorted_before_merging():
    token_spans = [(0, 2), (3, 8)]
    assert spans_for(token_spans, [1, 0]) == [{"start": 0, "end": 8}]


# --- end to end ---------------------------------------------------------------
# `token_spans` is optional on the finders, so the signature does not stop a
# fifth rule from emitting spanless matches. These do: every match `analyze`
# returns must carry spans that actually quote its own text.

def test_every_rule_returns_spans_that_quote_the_flagged_text():
    text = "تمت مراجعة الملف بشكل كامل من قبل المشرف، وقام الفريق بتحليل النتائج"
    matches = analyze(rules_path, whitelist_path, text)["matches"]

    assert {match["rule"] for match in matches} == {"بشكل", "تم", "قام بـ", "من قبل"}
    for match in matches:
        assert match["spans"], match
        quoted = " ".join(text[span["start"]:span["end"]] for span in match["spans"])
        assert dediac_ar(quoted) == match["flagged_phrase"], match


def test_spans_survive_diacritics_in_the_input():
    text = "تمّت مراجعةُ الملفِّ بشكلٍ كاملٍ"
    for match in analyze(rules_path, whitelist_path, text)["matches"]:
        quoted = " ".join(text[span["start"]:span["end"]] for span in match["spans"])
        assert dediac_ar(quoted) == match["flagged_phrase"], match


def test_a_repeated_phrase_gets_one_match_per_occurrence_at_its_own_offsets():
    text = "تم إغلاق الباب. تم إغلاق النافذة"
    matches = [m for m in analyze(rules_path, whitelist_path, text)["matches"]
               if m["rule"] == "تم"]

    assert len(matches) == 2
    assert matches[0]["spans"] != matches[1]["spans"]
    for match in matches:
        assert text[match["spans"][0]["start"]:match["spans"][0]["end"]] == "تم إغلاق"


def test_a_multi_word_agent_is_highlighted_only_to_its_head():
    """Ghaida's ruling, 2026-09-07: highlighting «من قبل وزير» out of
    «من قبل وزير الداخلية» is fine. The target has always been a single token,
    so 31% of من قبل matches on the held-out set stop mid-إضافة. That is
    accepted behaviour, not a defect — this pins it so it is not quietly
    "fixed" into a wider span later.
    """
    text = "تمت مراجعة الملف من قبل وزير الداخلية"
    match = [m for m in analyze(rules_path, whitelist_path, text)["matches"]
             if m["rule"] == "من قبل"][0]

    assert len(match["spans"]) == 1
    span = match["spans"][0]
    assert text[span["start"]:span["end"]] == "من قبل وزير"
    assert "الداخلية" not in text[span["start"]:span["end"]]


def test_a_separated_trigger_and_target_stay_two_spans():
    # the agent sits between them, and it is not part of the match
    text = "قام الباحث المتخصص بدراسة الظاهرة"
    match = [m for m in analyze(rules_path, whitelist_path, text)["matches"]
             if m["rule"] == "قام بـ"][0]

    assert len(match["spans"]) == 2
    assert text[match["spans"][0]["start"]:match["spans"][0]["end"]] == "قام"
    assert text[match["spans"][1]["start"]:match["spans"][1]["end"]] == "بدراسة"
    assert "الباحث" not in "".join(
        text[span["start"]:span["end"]] for span in match["spans"]
    )
