from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.dediac import dediac_ar

def preprocess(text):
    clean_text = dediac_ar(text)
    tokens = simple_word_tokenize(clean_text)
    return list(enumerate(tokens))
