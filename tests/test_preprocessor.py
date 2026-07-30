from app.text.preprocessor import preprocess


def test_preprocess_simple_sentence():
    result = preprocess("السلام عليكم")

    assert result == [
        (0, "السلام"),
        (1, "عليكم")
    ]

def test_preprocess_with_diacritics():
    result = preprocess("كَانَ الجَوُّ مُرْعِبًا")
    
    assert result == [
        (0, "كان"),
        (1, "الجو"),
        (2, "مرعبا")
    ]
    
def test_preprocess_with_no_diacritics():
    result = preprocess("تم المشروع بنجاح")
    
    assert result == [
        (0, "تم"),
        (1, "المشروع"),
        (2, "بنجاح")
    ]
    
def test_preprocess_with_whitespace():
    result = preprocess("بشكل   سريع    جدا")
    
    assert result == [
        (0, "بشكل"),
        (1, "سريع"),
        (2, "جدا")
    ]
    
def test_preprocess_with_trailing_spaces():
    result = preprocess(" بشكل سريع ")
    
    assert result == [
        (0, "بشكل"),
        (1, "سريع")
    ]
    
def test_preprocess_with_symbols():
    result = preprocess("كان الجو رهيب، بشكل عام.")
    
    assert result == [
        (0, "كان"),
        (1, "الجو"),
        (2, "رهيب"),
        (3, "،"),
        (4, "بشكل"),
        (5, "عام"),
        (6, ".")
    ]
    
def test_preprocess_when_empty():
    result = preprocess("")
    
    assert result == []
    
def test_preprocess_with_numbers():
    result = preprocess("تم بشكل كامل في عام 2026")
    
    assert result == [
        (0, "تم"),
        (1, "بشكل"),
        (2, "كامل"),
        (3, "في"),
        (4, "عام"),
        (5, "2026")
    ]