from app.engine.dictionary import is_masdar, is_transitive_verb

""" is_transitive_verb tests """


def test_is_transitive_verb_reads_arramooz_for_a_transitive_verb():
    assert is_transitive_verb("راجع") is True


def test_is_transitive_verb_reads_arramooz_for_an_intransitive_verb():
    assert is_transitive_verb("اتفق") is False


def test_is_transitive_verb_none_when_verb_not_in_arramooz():
    """An unknown verb is not evidence of transitivity — the caller must not
    flag on it."""
    assert is_transitive_verb("زززز") is None


def test_is_transitive_verb_force_list_overrides_arramooz():
    """Arramooz calls خرج transitive under a broad classical definition."""
    assert is_transitive_verb("خرج") is True
    assert is_transitive_verb("خرج", ["خرج"]) is False


def test_is_transitive_verb_force_list_only_removes_transitivity():
    """The list never grants transitivity to a verb Arramooz calls intransitive."""
    assert is_transitive_verb("اتفق", ["خرج"]) is False


def test_is_transitive_verb_force_list_does_not_touch_other_verbs():
    assert is_transitive_verb("راجع", ["خرج", "دخل"]) is True


def test_is_transitive_verb_empty_force_list():
    assert is_transitive_verb("خرج", []) is True




""" is_masdar tests """


def test_is_masdar_true_for_a_verbal_noun():
    assert is_masdar("إغلاق") is True


def test_is_masdar_true_for_measure_one_masdar():
    assert is_masdar("فتح") is True


def test_is_masdar_false_for_a_plain_noun():
    assert is_masdar("بيت") is False


def test_is_masdar_strips_the_definite_article():
    assert is_masdar("البيت") is False
    assert is_masdar("الإغلاق") is True


def test_is_masdar_none_when_word_is_absent_from_the_table():
    """Absence is not evidence — 5 of 195 real masdars are missing from the
    nouns table, so callers must proceed rather than suppress on None."""
    assert is_masdar("زززز") is None


def test_is_masdar_force_list_overrides_arramooz():
    """Arramooz records that أمر has a masdar sense, which is true but not what
    «تم الأمر بسرعة» means."""
    assert is_masdar("أمر") is True
    assert is_masdar("أمر", ["أمر"]) is False


def test_is_masdar_force_list_matches_the_definite_form_too():
    assert is_masdar("الأمر", ["أمر"]) is False


def test_is_masdar_force_list_does_not_touch_other_words():
    assert is_masdar("إغلاق", ["أمر"]) is True
