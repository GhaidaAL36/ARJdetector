from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.utils.dediac import dediac_ar


def get_pattern(word):
    db = MorphologyDB.builtin_db()
    analyzer = Analyzer(db)

    analyses = analyzer.analyze(word)
    word_patterns = [dediac_ar(a.get("pattern", "")) for a in analyses]
    return word_patterns


def matches_flagged_pattern(rules, pattern):
    has_flagged_pattern = any(p in rules["flagged_patterns"] for p in pattern)
    return has_flagged_pattern

def matches_nisba_pattern(pattern):
    has_flagged_pattern = any(p.endswith("ي") for p in pattern)
    return has_flagged_pattern

