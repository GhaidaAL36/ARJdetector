from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.utils.dediac import dediac_ar


def get_pattern(word):
    db = MorphologyDB.builtin_db()
    analyzer = Analyzer(db)

    analyses = analyzer.analyze(word)
    word_patterns = [dediac_ar(a.get("pattern", "")) for a in analyses]
    return word_patterns


def get_matches(word, rules, pattern):
    flag = False
    has_flagged_pattern = any(p in rules["flagged_patterns"] for p in pattern)

    if (
        word in rules["blacklisted_words"]
        or word.endswith(tuple(rules["flagged_suffixes"]))
        or word.startswith(tuple(rules["flagged_prefixes"]))
        or has_flagged_pattern
    ):
        flag = True

    return flag