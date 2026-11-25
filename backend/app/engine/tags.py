# --- pos ---
VERB = "verb"
NOUN = "noun"
ADJ = "adj"
NOUN_PROP = "noun_prop"
PART_NEG = "part_neg"
NOUN_QUANT = "noun_quant"
PREP = "prep"
PUNC = "punc"
CONJ = "conj"
CONJ_SUB = "conj_sub"
PART = "part"
PART_VERB = "part_verb"
PRON = "pron"
PRON_REL = "pron_rel"
PRON_DEM = "pron_dem"
PRON_INTERROG = "pron_interrog"
DIGIT = "digit"
ADV = "adv"
ADV_REL = "adv_rel"
ADV_INTERROG = "adv_interrog"
ABBREV = "abbrev"
FOREIGN = "foreign"

# --- proclitics ---
AL_DET = "Al_det"
BI_PREP = "bi_prep"

DESCRIPTOR_POS = frozenset({ADJ, NOUN, NOUN_PROP})

WAW_PROCLITICS = frozenset({"wa_part", "wa_conj", "wa_sub"})

#: "no proclitic in this slot". `na` appears on punctuation.
NO_PROCLITIC = frozenset({"0", "na", ""})

#: sentence-final punctuation. A comma is deliberately absent — it separates
#: chain members rather than ending the chain.
SENTENCE_END = frozenset({".", "!", "?", "؟", "۔"})

#: pos tags that cannot head a مضاف إليه: function words and punctuation.
#: A DENY-list, deliberately — the polarity is the safety property. An unknown
#: or newly-invented tag then FLAGS, which is the tolerated direction; an
#: allow-list would silence it, and a silent miss is the one thing the rule may
#: not do. Measured over 1,469 corpus occurrences of bare «من قبل»: the tags
#: outside both lists (pron_dem, pron_interrog, pron_rel, digit, foreign,
#: abbrev, verb) are 30 sentences, 26 of them real agents.
NON_GENITIVE_POS = frozenset({PUNC, PREP, CONJ, CONJ_SUB, PART, PRON})

#: pos tags that الأكثر/الأقلّ cannot be describing: function words,
#: punctuation, numerals. A DENY-list, same polarity as NON_GENITIVE_POS and
#: for the same reason — an unfamiliar tag then reaches the measure test and
#: may FLAG, which is the tolerated direction, whereas an allow-list would
#: silence it. Measured over 2,608 corpus occurrences of the trigger: these
#: stop 233, every one of them correctly (في 93 · منذ 18 · حتى 15 · على 13 ·
#: إلى 10 · أن · عن · خلال · لا · قد · هذا · التي · هو).
#:
#: `verb` is deliberately ABSENT. 76 occurrences of a real تمييز are tagged
#: verb in context (فقرا 58، فتكا 8، لفتا، شوقا، تعبا، فسادا…), and silencing
#: them would be missed عرنجية. Admitting every verb-tagged target costs one
#: extra occurrence in 300K once a preceding «على» is excluded, which is why
#: no shape test guards it (design C, ratified 2026-11-24).
NON_DESCRIBED_POS = frozenset(
    {
        PUNC, PREP, CONJ, CONJ_SUB, PART, PART_NEG, PART_VERB,
        PRON, PRON_REL, PRON_DEM, PRON_INTERROG,
        DIGIT, ADV, ADV_REL, ADV_INTERROG, ABBREV, FOREIGN,
    }
)

# --- Arabic orthography ---

PRONOUN_SUFFIXES = frozenset(
    {
        "ه", "ها", "هما", "هم", "هن",   # 3rd person
        "ك", "كما", "كم", "كن",         # 2nd person
        "ي", "نا",                      # 1st person
    }
)
