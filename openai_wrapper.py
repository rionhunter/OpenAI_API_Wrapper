import openai
import time
from openai import OpenAIError

DEFAULT_RETRIES = 3
RETRY_DELAY = 2  # seconds


def call_openai_method(method, *args, retries=DEFAULT_RETRIES, **kwargs):
    """
    Wraps any OpenAI API method with basic retry logic.
    
    Parameters:
        method: callable OpenAI method (e.g., openai.ChatCompletion.create)
        *args, **kwargs: passed to the OpenAI method
        retries: number of retry attempts on error
    Returns:
        Result of OpenAI method call
    Raises:
        Last OpenAIError if all retries fail
    """
    attempt = 0
    while attempt <= retries:
        try:
            return method(*args, **kwargs)
        except OpenAIError as e:
            if attempt == retries:
                raise
            time.sleep(RETRY_DELAY)
            attempt += 1
            print(f"Retrying OpenAI call due to error: {e} (attempt {attempt}/{retries})")
