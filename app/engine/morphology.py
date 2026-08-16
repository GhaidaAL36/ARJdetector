from camel_tools.utils.dediac import dediac_ar

WEAK_LETTERS = ["و", "ي", "ء"]
SHADDA = "ّ"
HAMZA_FORMS = "ءأإآئؤ"

VIII_INFIX_BY_RADICAL = {
    "ص": "ط",
    "ض": "ط",
    "ط": "ط",
    "ظ": "ط",
    "ز": "د",
    "د": "د",
    "ذ": "د",
}


def hollow_weak_letter_from_pattern(camel_root, raw_pattern):
    parts = camel_root.split(".")
    if len(parts) != 3 or parts[1] != "#" or "2" in raw_pattern:
        return None
    if "1" not in raw_pattern or "3" not in raw_pattern:
        return None

    middle = dediac_ar(raw_pattern[raw_pattern.index("1") + 1 : raw_pattern.index("3")])
    middle = middle.lstrip("ا")
    if middle.startswith("و"):
        return "و"
    if middle.startswith("ي"):
        return "ي"
    return None


def generate_root_candidates(camel_root, raw_pattern=""):
    parts = camel_root.split(".")
    if "#" not in parts:
        return ["".join(parts)]

    resolved_letter = hollow_weak_letter_from_pattern(camel_root, raw_pattern)
    if resolved_letter:
        return ["".join(resolved_letter if p == "#" else p for p in parts)]

    return [
        "".join(letter if p == "#" else p for p in parts) for letter in WEAK_LETTERS
    ]


def classify_measure(raw_pattern):
    has_shadda = SHADDA in raw_pattern

    if raw_pattern.startswith(("ٱِسْتَ", "ٱِسْتِ", "اِسْتَ", "اِسْتِ")):
        return "X"
    if raw_pattern.startswith(("ٱِنْ", "اِنْ")):
        return "VII"
    if raw_pattern.startswith(("ٱِ", "اِ")):
        if any(infix in raw_pattern for infix in ("تِ", "طِ", "دِ")):
            return "VIII"
        if len(raw_pattern) > 3 and "ت" in raw_pattern[2:5]:
            return "VIII"
        return "IV_or_VIII_unclear"
    if raw_pattern.startswith(("إِ", "أَ")):
        return "IV"
    if raw_pattern.startswith("م") and "1ا" in raw_pattern:
        return "III"
    if raw_pattern.startswith("ت"):
        if has_shadda and "ا" not in raw_pattern:
            return "V"
        if "ا" in raw_pattern[:4] and not has_shadda:
            return "VI"
        if (
            "ِي" in raw_pattern
            or "ْيِي" in raw_pattern
            or ("ْ" in raw_pattern and "ي" in raw_pattern)
        ):
            return "II"
        if has_shadda:
            return "V"
        return "V_or_VI_unclear"
    return "I"


def same_radical(letter, root_letter):
    return _normalize_hamza(letter) == _normalize_hamza(root_letter)


def _normalize_hamza(letter):
    return "ء" if letter in HAMZA_FORMS else letter


def _root_options(root_field):
    return [option for option in root_field.split(";") if option]


def verb_matches_measure(verb_row, measure):
    verb = verb_row["unvocalized"]
    has_shadda = SHADDA in verb_row["vocalized"]
    root = verb_row.get("root", "")
    roots = _root_options(root)

    def is_first_radical(index):
        """Does the verb hold a first radical at this index? True when the row
        carries no root to check against."""
        if not roots:
            return True
        if index >= len(verb):
            return False
        return any(same_radical(verb[index], option[0]) for option in roots)

    if measure == "X":
        return verb.startswith("است") and is_first_radical(3)

    if measure == "VIII":
        if len(verb) < 4:
            return False
        if verb[1] == "ت":
            return True
        if verb[2] != VIII_INFIX_BY_RADICAL.get(verb[1], "ت"):
            return False
        return is_first_radical(1)

    if measure == "VII":
        return verb.startswith("ان") and is_first_radical(2)

    if measure == "IV":
        if verb.startswith(("ان", "است")):
            return False
        if not verb.startswith(("أ", "ا")):
            return False
        if len(verb) >= 4 and "ت" in verb[1:3] and "ت" not in root:
            return False
        return True

    if measure == "III":
        return len(verb) == 4 and verb[1] == "ا" and is_first_radical(0)

    if measure == "VI":
        return verb.startswith("ت") and len(verb) >= 4 and "ا" in verb

    if measure == "V":
        return verb.startswith("ت") and not verb.startswith("است")

    if measure == "II":
        return len(verb) == 3 and has_shadda

    if measure == "I":
        return len(verb) == 3 and not has_shadda

    return True
