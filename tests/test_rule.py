from app.engine.rule import get_pattern, matches_flagged_pattern, matches_nisba_pattern

""" get_pattern """

def test_get_pattern_faael():
    patterns = get_pattern("غاضب")

    assert "1ا23" in patterns


def test_get_pattern_faeel():
    patterns = get_pattern("كبير")

    assert "12ي3" in patterns


def test_non_flagged_pattern():
    patterns = get_pattern("مثلث")

    assert "م123" in patterns
    assert "1ا23" not in patterns
    assert "12ي3" not in patterns
    
def test_get_pattern_unrecognized_word():
    patterns = get_pattern("test")
    
    assert 'FOREIGN' in patterns 
    
def test_get_pattern_gibberish_word():
    patterns = get_pattern("هيسباكخب")
    
    assert [] == patterns 
    
""" matches_flagged_pattern """
    
def test_all_patterns_are_flagged():
    rules = {
        "flagged_patterns": ["1ا23", "12ي3"]
    }

    patterns = ["1ا23", "12ي3"]

    assert matches_flagged_pattern(rules, patterns) is True
    
def test_one_pattern_is_flagged():
    rules = {
        "flagged_patterns": ["1ا23", "12ي3"]
    }

    patterns = ["م123", "1ا23"]

    assert matches_flagged_pattern(rules, patterns) is True
    
def test_no_pattern_is_flagged():
    rules = {
        "flagged_patterns": ["1ا23", "12ي3"]
    }

    patterns = ["م123"]

    assert matches_flagged_pattern(rules, patterns) is False
    
def test_unrecognized_word_pattern():
    rules = {
            "flagged_patterns": ["1ا23", "12ي3"]
        }
    
    pattern = []
    
    assert matches_flagged_pattern(rules, pattern) is False
    
""" matches_nisba_pattern test """
    
def test_matches_nisba_pattern():
    patterns = ["م123", "123ي"]

    assert matches_nisba_pattern(patterns) is True
    
def test_no_nisba_pattern():
    patterns = ["1ا23", "م123"]

    assert matches_nisba_pattern(patterns) is False
    
def test_one_of_multiple_patterns_is_nisba():
    patterns = ["1ا23", "م123", "123ي"]

    assert matches_nisba_pattern(patterns) is True
    
def test_empty_pattern():
    patterns = []

    assert matches_nisba_pattern(patterns) is False