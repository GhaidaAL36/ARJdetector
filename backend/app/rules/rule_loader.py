import json

def reader(path):
    with open(path, 'r') as json_file:
        raw_text = json_file.read()

    parsed_data = json.loads(raw_text)

    return parsed_data
