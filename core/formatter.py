import re
import json
import logging

def clean_json_output(raw_text):
    import json

    start = raw_text.find('[')
    end = raw_text.rfind(']')

    if start != -1 and end != -1:
        try:
            return json.loads(raw_text[start:end+1])
        except json.JSONDecodeError:
            pass

    return []