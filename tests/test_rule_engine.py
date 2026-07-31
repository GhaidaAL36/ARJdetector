from app.engine.rule_engine import find_flagged_words

""" find_flagged_words test """

def test_find_flagged_words():
    rules = {
        "trigger_word": "بشكل"
        }
     
    text = "تم بشكل سريع"
    
    result = find_flagged_words(rules, text)
    
    assert result == ["سريع"]

def test_trigger_word_at_end():
    rules = {
        "trigger_word": "بشكل"
    }

    text = "تم بشكل"

    result = find_flagged_words(rules, text)

    assert result == []
    
def test_no_trigger_word():
    rules = {
        "trigger_word": "بشكل"
    }

    text = "تم المشروع بنجاح"

    result = find_flagged_words(rules, text)

    assert result == []
    
def test_multiple_trigger_words():
    rules = {
        "trigger_word": "بشكل"
    }

    text = "تم بشكل سريع وبشكل واضح"

    result = find_flagged_words(rules, text)

    assert result == ["سريع", "واضح"]
    
def test_trigger_word_at_end_of_word():
    rules = {
        "trigger_word": "بشكل"
    }

    text = "تم وبشكل سريع"

    result = find_flagged_words(rules, text)

    assert result == ["سريع"]