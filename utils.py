import os
import json
from datetime import datetime

def load_prompt_from_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_text_to_file(content, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved to {path}")

def format_as_json_response(content, model, mode):
    return json.dumps({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": model,
        "mode": mode,
        "response": content
    }, indent=2)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
