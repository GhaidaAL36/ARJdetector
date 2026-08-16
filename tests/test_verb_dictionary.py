from app.engine.verb_dictionary import is_transitive_verb

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


