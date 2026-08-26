# --- pos ---
VERB = "verb"
NOUN = "noun"
ADJ = "adj"
NOUN_PROP = "noun_prop"
PART_NEG = "part_neg"
NOUN_QUANT = "noun_quant"

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
