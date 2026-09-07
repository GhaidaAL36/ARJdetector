from app.engine.analysis import analyze_word
from app.engine.morphology import (
    SHADDA,
    classify_measure,
    generate_root_candidates,
    verb_matches_measure,
)
from app.engine.dictionary import lookup_verbs_by_root
from app.engine.tags import NOUN

TRUSTED_DERIVATION_STATUSES = {
    "forced",
    "unique_match",
    "shadda_disambiguated",
    "stem_disambiguated",
    "still_ambiguous",
}

def derive_base_verb(masdar, force_derived_verbs=None):
    forced = get_forced_base_verb(masdar, force_derived_verbs or {})
    if forced:
        return forced, "forced"

    analyses = analyze_word(masdar)
    if not analyses:
        return None, "no_camel_analysis"

    noun_analyses = [a for a in analyses if a.get("pos") == NOUN]
    analysis = noun_analyses[0] if noun_analyses else analyses[0]

    camel_root = analysis.get("root", "")
    raw_pattern = analysis.get("pattern", "")

    if raw_pattern.startswith("ال"):
        raw_pattern = raw_pattern[2:]
        masdar = masdar[2:]

    measure = classify_measure(raw_pattern)
    masdar_has_shadda = SHADDA in raw_pattern

    candidates = lookup_verbs_by_root(
        generate_root_candidates(camel_root, raw_pattern)
    )
    if not candidates:
        return None, "no_arramooz_root_match"

    matching = [row for row in candidates if verb_matches_measure(row, measure)]
    if not matching:
        return None, "no_measure_match"
    if len({row["unvocalized"] for row in matching}) == 1:
        return matching[0]["unvocalized"], "unique_match"

    shadda_matched = [
        row for row in matching if (SHADDA in row["vocalized"]) == masdar_has_shadda
    ]
    pool = shadda_matched if shadda_matched else matching
    if len(pool) == 1:
        return pool[0]["unvocalized"], "shadda_disambiguated"

    if masdar.endswith("ة"):
        stem_matched = [row for row in pool if row["unvocalized"] == masdar[:-1]]
        if len(stem_matched) == 1:
            return stem_matched[0]["unvocalized"], "stem_disambiguated"

    def distance(row):
        return abs(len(row["unvocalized"]) - len(masdar))

    closest = min(distance(row) for row in pool)
    tied = [row for row in pool if distance(row) == closest]
    if len(tied) == 1:
        return tied[0]["unvocalized"], "length_disambiguated"

    return tied[0]["unvocalized"], "still_ambiguous"


def get_forced_base_verb(masdar, force_derived_verbs):
    if masdar in force_derived_verbs:
        return force_derived_verbs[masdar]
    if masdar.startswith("ال"):
        return force_derived_verbs.get(masdar[2:])
    return None


def is_trusted_derivation(status):
    return status in TRUSTED_DERIVATION_STATUSES
