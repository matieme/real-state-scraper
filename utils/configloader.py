import json
import codecs


def load_config(file_path):
    with codecs.open(file_path, 'r', 'utf-8-sig') as file:
        config = json.load(file)
    return config
