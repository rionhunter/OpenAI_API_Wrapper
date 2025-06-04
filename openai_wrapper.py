import openai
import time
from openai import OpenAIError
import os
import json
import logging

DEFAULT_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Configure module logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    # Log the request payload
    logger.debug("OpenAI Request: method=%s, args=%s, kwargs=%s", method_path, args, kwargs)

    attempt = 0
    while attempt <= retries:
        try:
            return method_func(*args, **kwargs)
        except OpenAIError as e:
            if "BadRequestError" in str(type(e)):
                logger.error("OpenAI BadRequestError: %s", e)
                print("Pausing for debugging. Choose an option:")
                print("1: Retry the OpenAI call")
                print("2: Continue to the next file")
                print("3: Terminate the pipeline")

                choice = input("Enter your choice (1, 2, or 3): ")

                if choice == "1":
                    attempt = 0  # Reset attempt counter to retry
                    continue
                elif choice == "2":
                    return None  # Return None to signal skipping the file
                elif choice == "3":
                    raise  # Re-raise the exception to terminate the pipeline
                else:
                    logger.warning("Invalid choice. Retrying the OpenAI call.")
                    attempt = 0
                    continue
            if attempt == retries:
                raise
            time.sleep(RETRY_DELAY)
            attempt += 1
            logger.warning("Retrying OpenAI call due to error: %s (attempt %s/%s)", e, attempt, retries)


def generate_content(prompt: str, api_key: str, model: str = "gpt-4") -> str | None:
    """Send a prompt to the OpenAI chat completion API and return the content."""

    messages = [{"role": "user", "content": prompt}]
    logger.debug("Generating content with model %s", model)

    try:
        response = call_openai_method(
            "chat.completions.create",
            model=model,
            messages=messages,
            temperature=0.7,
            api_key=api_key,
        )
        if response:
            return response.choices[0].message.content.strip()
        return None
    except Exception as e:
        logger.error("OpenAI call failed: %s", e)
        return None


def generate_content_v2(prompt: str, api_key: str, model: str):
    """Alternative content generation method with manual retry logic."""

    openai.api_key = api_key
    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            messages = [{"role": "user", "content": prompt}]
            response = openai.chat.completions.create(
                model=model,
                messages=json.dumps(messages),
                temperature=0.0,
                # max_tokens=max_tokens,  # Consider re-introducing if needed
            )
            return response.choices[0].message.content
        except openai.APIConnectionError as e:
            logger.warning(
                "Retrying OpenAI call due to error: %s (attempt %s/%s)",
                e,
                attempt + 1,
                max_retries,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
        except openai.APIError as e:
            logger.warning(
                "Retrying OpenAI call due to error: %s (attempt %s/%s)",
                e,
                attempt + 1,
                max_retries,
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise
        except Exception as e:
            logger.error("OpenAI call failed: %s", e)
            raise
