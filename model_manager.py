import os
import json
import openai

CONFIG_FILE = 'model_config.json'


def get_available_models():
    """Returns model list from local config if exists. If file doesn't exist or is incomplete, updates from OpenAI."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data.get("models"), list) and data["models"]:
                    return data["models"]
            except json.JSONDecodeError:
                pass

    return update_model_config()


def update_model_config():
    """Fetches models from OpenAI and updates the local config."""
    try:
        response = openai.Model.list()
        models = sorted(m['id'] for m in response['data'])
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"models": models}, f, indent=2)
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
