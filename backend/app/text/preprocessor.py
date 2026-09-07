from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.dediac import dediac_ar

def preprocess(text):
    clean_text = dediac_ar(text)
    tokens = simple_word_tokenize(clean_text)
    return list(enumerate(tokens))


def _kept_indices(text, clean_text):
    kept = []
    position = 0
    for character in clean_text:
        while text[position] != character:
            position += 1
        kept.append(position)
        position += 1
    return kept


def align_tokens(text, tokens):
    clean_text = dediac_ar(text)
    kept = _kept_indices(text, clean_text)
    kept_set = set(kept)

    spans = []
    cursor = 0
    for _, token in tokens:
        found = clean_text.index(token, cursor)
        start = kept[found]
        end = kept[found + len(token) - 1] + 1
        while end < len(text) and end not in kept_set:
            end += 1
        spans.append((start, end))
        cursor = found + len(token)

    return spans
