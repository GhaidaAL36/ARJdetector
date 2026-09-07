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
PRON = "pron"

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

# --- Arabic orthography ---

PRONOUN_SUFFIXES = frozenset(
    {
        "ه", "ها", "هما", "هم", "هن",   # 3rd person
        "ك", "كما", "كم", "كن",         # 2nd person
        "ي", "نا",                      # 1st person
    }
)
