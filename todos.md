# TODOs

The following areas could be improved or expanded upon in the project:

1. **Automated Testing**
   - Increase test coverage for the primary API modules (`Gpt_Api_Module`, `Dalle_Api_Module`, and `Whisper_Api_Module`).
   - Provide mocking of OpenAI API responses to allow tests to run without a network connection.

2. **Error Handling and Logging**
   - Replace interactive prompts in `openai_wrapper.call_openai_method` with exceptions or configurable callbacks so that automated pipelines are not blocked.
   - Use consistent logging across modules instead of `print` statements for user-facing errors.

3. **Input Validation**
   - Add validation of CLI arguments (e.g. prompt length, file existence) to prevent errors before API calls.

4. **Documentation**
   - Consolidate README information and add short module docstrings describing expected behaviour and return values.

5. **GUI Enhancements**
   - The GUI tools are minimal; consider expanding them or documenting them as examples only.

6. **Configuration Management**
   - Allow specifying a custom path for `model_config.json` and support environment configuration options.
