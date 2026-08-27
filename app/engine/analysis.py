from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.utils.dediac import dediac_ar

from app.text.normalize import normalize_lookup_key

_mle = None
_analyzer = None

UNANALYSED = {
    "pos": "",
    "pattern": "",
    "lex": "",
    "prc0": "0",
    "prc1": "0",
    "prc2": "0",
}


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
        if not entry.analyses:
            results.append(dict(UNANALYSED))
            continue

        top_analysis = entry.analyses[0].analysis
        pos = top_analysis.get("pos", "")
        pattern = dediac_ar(top_analysis.get("pattern", ""))
        lex = normalize_lookup_key(dediac_ar(top_analysis.get("lex", "")))
        prc2 = top_analysis.get("prc2", "")
        prc1 = top_analysis.get("prc1", "")
        prc0 = top_analysis.get("prc0", "")
        results.append(
            {
                "pos": pos,
                "pattern": pattern,
                "lex": lex,
                "prc0": prc0,
                "prc1": prc1,
                "prc2": prc2,
            }
        )

    return results


def analyze_word(word):
    return _get_analyzer().analyze(word)
