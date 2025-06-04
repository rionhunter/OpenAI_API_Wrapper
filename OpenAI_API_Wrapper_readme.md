# OpenAI CLI Toolkit

This toolkit provides a unified command-line interface for interacting with OpenAI’s GPT, DALL·E, and Whisper APIs, along with automatic model validation, retry logic, and GUI diagnostics.

## Setup

1. **Install dependencies**:

   ```bash
   pip install openai
   ```

2. **Set your OpenAI API Key** (or provide via `--api_key` flag):

   ```bash
   export OPENAI_API_KEY='your-api-key'
   ```

3. **Directory Overview**:

   * `entrypoint.py`: Unified entry point (gpt | dalle | whisper) for both CLI and import.
   * `Gpt_Api_Module.py`: GPT chat and assistant functions.
   * `Dalle_Api_Module.py`: DALL·E image generation.
   * `Whisper_Api_Module.py`: Audio transcription/translation.
   * `model_manager.py`: Maintains and updates model list.
   * `openai_wrapper.py`: Unified retry-safe OpenAI client wrapper.
   * `testing_gui.py`: GUI interface for API testing and debugging.
   * `demo_runner.py`: Cycles through all APIs for demonstration.
   * `utils.py`: Miscellaneous utilities.

## Usage

### CLI Format

```bash
python entrypoint.py <mode> --model <model-name> [flags]
```

### GPT Example

```bash
python entrypoint.py gpt \
  --model gpt-4 \
  --prompt "Explain the Fermi Paradox" \
  --stream \
  --json_output \
  --output_file output.txt \
  --api_key sk-xxxxx
```

### DALL·E Example

```bash
python entrypoint.py dalle \
  --model dall-e-3 \
  --prompt "Retro-futuristic city skyline" \
  --size 1024x1024 \
  --quality hd \
  --output_dir images
```

### Whisper Example

```bash
python entrypoint.py whisper \
  --model whisper-1 \
  --file ./audio.mp3 \
  --format json \
  --translate \
  --language en
```

## Traceback & Error Handling

* All API calls are wrapped with retry logic (default 3 attempts).
* Failures raise exceptions, and CLI usage prints full tracebacks.
* When used as a Python module, exceptions propagate upward.

## Model Management

* Uses local `model_config.json`, which stores a list of verified model names.
* By default, this list is only updated **once per week** to minimize API calls.
* On attempted use of an unknown model, `model_manager` will:

  1. Check if an update is due based on timestamp.
  2. Fetch the updated list from OpenAI **only if needed**.
  3. Cache it locally for subsequent calls.
* Safe to import without triggering unintended API calls.

You can access or refresh the list directly:

```python
from model_manager import get_available_models, update_model_config

# Get list of known OpenAI model IDs
models = get_available_models()

# Force a refresh from OpenAI (optional)
update_model_config(api_key="your-key")
```

## GUI Testing Tool

```bash
python entrypoint.py
```

Launching with no args opens a live test GUI for GPT interaction.

## Automated Tests

Run the simple launcher to execute all test scripts in the `tests/` folder. Pass
an API key if you wish to run live API tests:

```bash
python test_launcher.py --api_key YOUR_KEY
```

## Features

* Modern OpenAI client integration
* Fully import-safe modules (no auto-execution on import)
* Per-call API key injection
* Unified error and timing diagnostics
* GUI fallback when run without args

## Requirements

* Python 3.7+
* `openai >= 1.0.0`

---

For detailed API usage, visit [OpenAI’s API reference](https://platform.openai.com/docs/api-reference).
