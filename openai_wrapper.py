import openai
import time
from openai import OpenAIError
import os

DEFAULT_RETRIES = 3
RETRY_DELAY = 2  # seconds


def call_openai_method(method_path, *args, retries=DEFAULT_RETRIES, **kwargs):
    """
    Call an OpenAI method via string path, like 'chat.completions.create'.
    Example: call_openai_method("chat.completions.create", model="gpt-4", ...)
    """
    api_key = kwargs.pop('api_key', os.getenv("OPENAI_API_KEY"))
    client = openai.OpenAI(api_key=api_key)

    parts = method_path.split(".")
    method_func = client
    for part in parts:
        method_func = getattr(method_func, part)

    attempt = 0
    while attempt <= retries:
        try:
            return method_func(*args, **kwargs)
        except OpenAIError as e:
            if attempt == retries:
                raise
            time.sleep(RETRY_DELAY)
            attempt += 1
            print(f"Retrying OpenAI call due to error: {e} (attempt {attempt}/{retries})")


def generate_content(prompt: str, api_key: str, model: str = "gpt-4") -> str:
    """
    Send a prompt to the OpenAI chat completion API and return the content.
    """
    response = call_openai_method(
        "chat.completions.create",
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        api_key=api_key
    )
    return response.choices[0].message.content.strip()
