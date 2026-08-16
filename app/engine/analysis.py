from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.utils.dediac import dediac_ar

_mle = None
_analyzer = None


def _get_mle():
    global _mle
    if _mle is None:
        _mle = MLEDisambiguator.pretrained()
    return _mle


def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = Analyzer(MorphologyDB.builtin_db())
    return _analyzer


def get_pos_and_pattern_in_context(tokens):
    mle = _get_mle()
    words = [word for _, word in tokens]
    disambiguated = mle.disambiguate(words)

    results = []
    for entry in disambiguated:
        top_analysis = entry.analyses[0].analysis
        pos = top_analysis.get("pos", "")
        pattern = dediac_ar(top_analysis.get("pattern", ""))
        lex = dediac_ar(top_analysis.get("lex", ""))
        results.append({"pos": pos, "pattern": pattern, "lex": lex})

    return results


def analyze_word(word):
    return _get_analyzer().analyze(word)
