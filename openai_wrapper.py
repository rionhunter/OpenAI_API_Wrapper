import openai
import time
from openai import OpenAIError
import os
import json
import logging
import argparse
import sys

DEFAULT_RETRIES = 3
RETRY_DELAY = 2  # seconds

if __name__ == "__main__":
    # Add argument parser for verbosity level
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity", type=str, default="DEBUG", help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    args = parser.parse_args()

    # Configure logging level from arguments
    log_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(log_level, int):
        print(f"Invalid log level: {args.verbosity}. Defaulting to DEBUG.")
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
    )
else:
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
    )


def call_openai_method(method_path, task_id, *args, retries=DEFAULT_RETRIES, auto_retry_mode=None, **kwargs):
    """
    Call an OpenAI method via string path, like 'chat.completions.create'.
    auto_retry_mode: None (default, interactive), or one of 'retry', 'skip', 'abort'.
    """
    api_key = kwargs.pop("api_key", os.getenv("OPENAI_API_KEY"))
    client = openai.OpenAI(api_key=api_key)

    parts = method_path.split(".")
    method_func = client
    for part in parts:
        method_func = getattr(method_func, part)

    # Log the request payload
    logging.debug(
        f"[Task ID: {task_id}] OpenAI Request: method={method_path}, args={args}, kwargs={kwargs}"
    )

    attempt = 0
    while attempt <= retries:
        try:
            return method_func(*args, **kwargs)
        except OpenAIError as e:
            logging.error(f"[Task ID: {task_id}] OpenAIError: {e}")
            if "BadRequestError" in str(type(e)):
                if auto_retry_mode is None:
                    print(f"[Task ID: {task_id}] OpenAI BadRequestError: {e}")
                    print("Pausing for debugging. Choose an option:")
                    print("1: Retry the OpenAI call")
                    print("2: Continue to the next file")
                    print("3: Terminate the pipeline")
                    choice = input("Enter your choice (1, 2, or 3): ")
                else:
                    # Non-interactive mode: auto select
                    if auto_retry_mode == 'retry':
                        choice = "1"
                    elif auto_retry_mode == 'skip':
                        choice = "2"
                    elif auto_retry_mode == 'abort':
                        choice = "3"
                    else:
                        choice = "1"  # Default to retry
                if choice == "1":
                    attempt = 0  # Reset attempt counter to retry
                    logging.info(f"[Task ID: {task_id}] Retrying OpenAI call (manual/auto)")
                    continue
                elif choice == "2":
                    logging.warning(f"[Task ID: {task_id}] Skipping file due to error.")
                    return None  # Return None to signal skipping the file
                elif choice == "3":
                    logging.critical(f"[Task ID: {task_id}] Aborting pipeline due to error.")
                    raise  # Re-raise the exception to terminate the pipeline
                else:
                    print("Invalid choice. Retrying the OpenAI call.")
                    attempt = 0
                    continue
            if attempt == retries:
                logging.critical(f"[Task ID: {task_id}] Max retries reached. Raising error.")
                raise
            time.sleep(RETRY_DELAY)
            attempt += 1
            logging.warning(
                f"[Task ID: {task_id}] Retrying OpenAI call due to error: {e} (attempt {attempt}/{retries})"
            )
    return None


