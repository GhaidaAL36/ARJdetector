from app.rules.rule_loader import reader
import json
import pytest



def test_reader_valid_json(tmp_path):
    expected = {
        "trigger_word": "بشكل",
        "flagged_patterns": ["1ا23"],
        "whitelisted_words": ["عام", "خاص"],
    }
    
    file = tmp_path / "rules.json"
    file.write_text(json.dumps(expected), encoding="utf-8")
    
    result = reader(file)
    
    assert result == expected
    

def test_reader_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        reader("does_not_exist.json")


def test_reader_invalid_json(tmp_path):
    file = tmp_path / "invalid.json"
    file.write_text('{"trigger_word": "بشكل"', encoding="utf-8")
    
    with pytest.raises(json.JSONDecodeError):
        reader(file)

def test_reader_empty_file(tmp_path):
    file = tmp_path / "empty.json"
    file.write_text("", encoding="utf-8")
    
    with pytest.raises(json.JSONDecodeError):
        reader(file)