# OpenAI GPT API Client

This CLI tool allows you to interact with OpenAI's GPT models using either the Chat Completions API or the Assistants API. It dynamically verifies and syncs available model IDs via a local configuration system.

## Setup

1. **Install dependencies**:

   ```bash
   pip install openai
   ```

2. **Create/Open Configuration File**:
   Ensure you have a file named `model_config.json` in the same directory. It will be updated automatically to track valid OpenAI model names.

3. **Set API Key**:
   Set your OpenAI API key as an environment variable or pass it via `--api_key`:

   ```bash
   export OPENAI_API_KEY='your-api-key'
   ```

## Usage

### Basic Command

```bash
python main.py --agent chat --model gpt-4-turbo --prompt "Say something smart."
```

### With Prompt from File

```bash
python main.py --agent chat --model gpt-3.5-turbo --prompt_file ./my_prompt.txt
```

### Streaming Mode

```bash
python main.py --agent chat --model gpt-4-turbo --prompt "Stream this please" --stream
```

### Using the Assistants API

```bash
python main.py --agent assistant --model gpt-4-turbo --assistant_id asst_abc123 --prompt "Assist me!"
```

### JSON Output Mode

```bash
python main.py --agent chat --model gpt-3.5-turbo --prompt "Return structured response" --json_output
```

### Save Response to File

```bash
python main.py --agent chat --model gpt-4 --prompt "Save me" --output_file result.txt
```

## How It Works

* Validates the provided model against a local `model_config.json`.
* If the model is not found, it will fetch the latest list from OpenAI.
* The script supports both prompt strings and input files.
* Optional streaming output, JSON formatting, and saving to a file.

## Dependencies

* Python 3.7+
* `openai`

## Files

* `main.py`: Main entry script for command line usage.
* `model_manager.py`: Handles model config sync and validation.
* `model_config.json`: Auto-managed file of available OpenAI model IDs.

## Coming Soon

* Shared model config support for DALL·E and Whisper.
* GUI manager for model config.

---

For detailed model specs and pricing, refer to [OpenAI’s model documentation](https://platform.openai.com/docs/models).
