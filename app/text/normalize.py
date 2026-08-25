ALIF_WASLA = "ٱ"
ALIF = "ا"


def normalize_lookup_key(text):
    if not text:
        return text
    return text.replace(ALIF_WASLA, ALIF)
