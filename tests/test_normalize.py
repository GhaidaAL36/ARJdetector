import pytest

from app.text.normalize import ALIF, ALIF_WASLA, normalize_lookup_key

""" normalize_lookup_key tests """


def test_normalize_folds_alif_wasla_to_plain_alif():
    assert normalize_lookup_key("ٱكتشاف") == "اكتشاف"


def test_normalize_folds_alif_wasla_anywhere_in_the_word():
    assert normalize_lookup_key("بٱكتشاف") == "باكتشاف"


def test_normalize_leaves_a_plain_alif_alone():
    assert normalize_lookup_key("اكتشاف") == "اكتشاف"


@pytest.mark.parametrize("word", ["إصلاح", "أمر", "آثار", "مسألة", "شيء"])
def test_normalize_does_not_touch_the_other_hamza_carriers(word):
    """Arramooz stores أ / إ / آ faithfully — إصلاح is present and اصلاح is not.
    Folding them would turn working lookups into silent misses."""
    assert normalize_lookup_key(word) == word


def test_normalize_is_idempotent():
    once = normalize_lookup_key("ٱستقالة")

    assert normalize_lookup_key(once) == once


def test_normalize_preserves_length():
    """A one-for-one substitution — token offsets downstream must not shift."""
    word = "ٱجتماع"

    assert len(normalize_lookup_key(word)) == len(word)


def test_normalize_folds_every_occurrence_in_one_string():
    """str.replace is global, but pin it — a later switch to a prefix-only fold
    would silently change what a multi-word key resolves to."""
    assert normalize_lookup_key("ٱكتشاف ٱستقالة") == "اكتشاف استقالة"


def test_normalize_folds_selectively_within_one_string():
    """The two decisions have to hold at once: ٱ goes, إ stays, in one key."""
    assert normalize_lookup_key("ٱتفاق إصلاح") == "اتفاق إصلاح"


def test_normalize_folds_a_bare_alif_wasla():
    assert normalize_lookup_key(ALIF_WASLA) == ALIF


@pytest.mark.parametrize("letter", ["ٲ", "ٳ", "ٵ"])
def test_normalize_leaves_the_neighbouring_codepoints_alone(letter):
    """U+0672/0673/0675 sit next to alif wasla in the block and are distinct
    letters. Only U+0671 is measured absent from Arramooz, so only it folds."""
    assert normalize_lookup_key(letter) == letter


def test_normalize_handles_an_empty_string():
    assert normalize_lookup_key("") == ""


def test_normalize_passes_none_through():
    """derive_base_verb and the whitelist readers can hand back None; the
    normalizer must not be the thing that raises."""
    assert normalize_lookup_key(None) is None


def test_normalize_leaves_non_arabic_text_alone():
    assert normalize_lookup_key("hello 123") == "hello 123"


def test_the_two_codepoints_are_the_ones_intended():
    """Guards against an editor silently rewriting the literals in the module."""
    assert ALIF_WASLA == "ٱ"
    assert ALIF == "ا"
