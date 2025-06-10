# UX > Data Flow > Result Pipeline Summary

This document provides an overview of how a user interacts with the project and how data flows through the modules to produce a result.

## UX (User Experience)

The toolkit exposes a command line interface via `entrypoint.py` and a GUI when launched without arguments. The CLI accepts a `mode` (`gpt`, `dalle`, or `whisper`) and various parameters such as `--model`, `--prompt`, or `--file` depending on the mode. When started without parameters, it attempts to launch the diagnostic GUI defined in `testing_gui.py`.

Key lines in `entrypoint.py` illustrate this behaviour:

```
15  if is_direct and len(sys.argv) == 1:
16      try:
17          from testing_gui import OpenAITestGUI
18          import tkinter as tk
19          root = tk.Tk()
20          app = OpenAITestGUI(root)
21          root.mainloop()
```

When arguments are supplied, `argparse` parses them and selects the appropriate API function.

```
34      parser = argparse.ArgumentParser(description='Unified OpenAI CLI')
36      parser.add_argument('mode', choices=['gpt', 'dalle', 'whisper'], help='Operation mode')
...
67      if args.mode == 'gpt':
68          if args.assistant_id:
69              result = use_assistant_api(args.prompt, args.assistant_id, args.api_key)
71          else:
72              result = use_chat_api(args.prompt, args.model, args.stream, args.api_key)
```

## Data Flow

1. **Model Validation** – Before each API call, the selected model is validated using `model_manager.confirm_model()` which checks the local `model_config.json` or updates it from OpenAI if necessary.
2. **API Calls** – Each API module (`Gpt_Api_Module`, `Dalle_Api_Module`, `Whisper_Api_Module`) constructs request parameters and invokes `openai_wrapper.call_openai_method()` to interact with the OpenAI API. The wrapper handles retries and error prompts.
3. **Result Handling** – The CLI optionally formats GPT output as JSON and can save text or image URLs to files. The GUI allows saving responses through UI controls.

## Result Pipeline

- User triggers a command (`gpt`, `dalle`, or `whisper`) via CLI or GUI.
- The selected module builds a request payload (e.g. `generate_dalle_image()` creates an image generation payload with model, prompt, size, etc.).
- `call_openai_method()` sends the request to the OpenAI API with retry logic. Errors of type `BadRequestError` prompt the user to retry, skip, or abort.
- Successful responses are printed, returned, or saved to disk via `utils.save_text_to_file` or direct file writes in each module.
- For GPT, optional JSON formatting is implemented:

```
72              if args.json_output:
73                  import json
74                  from datetime import datetime
75                  result = json.dumps({
76                      "timestamp": datetime.utcnow().isoformat() + "Z",
77                      "model": args.model,
78                      "mode": args.mode,
79                      "response": result
80                  }, indent=2)
```

This pipeline ensures user input flows through argument parsing, model validation, API invocation, and results output in a unified manner.
