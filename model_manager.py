import os
import json
import openai
import time

CONFIG_FILE = 'model_config.json'
MAX_CACHE_AGE = 7 * 24 * 3600  # 1 week in seconds

def get_available_models(api_key=None):
    """Returns model list from local config if exists. If missing, stale, or invalid, updates from OpenAI."""
    if os.path.exists(CONFIG_FILE):
        mtime = os.path.getmtime(CONFIG_FILE)
        age = time.time() - mtime
        print(f"Model config last modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}")

        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data.get("models"), list) and data["models"]:
                if age > MAX_CACHE_AGE and api_key:
                    print("Model cache older than 1 week. Refreshing...")
                    return update_model_config(api_key=api_key)
                print(f"Loaded {len(data['models'])} cached models.")
                return data["models"]
        except json.JSONDecodeError:
            print("Failed to parse model config; attempting update.")

    if api_key:
        return update_model_config(api_key=api_key)
    return []

def update_model_config(api_key=None):
    """Fetches models from OpenAI and updates the local config."""
    try:
        client = openai.OpenAI(api_key=api_key) if api_key else openai
        response = client.models.list()
        models = sorted(m.id for m in response.data)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                "models": models,
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }, f, indent=2)
        print(f"Model config updated successfully. {len(models)} models saved.")
        return models
    except Exception as e:
        print(f"Error updating models from OpenAI: {e}")
        return []

def confirm_model(model_name):
    """Confirms if a model is in the current config; updates config if not found."""
    models = get_available_models()
    if model_name not in models:
        models = update_model_config()
    return model_name in models
