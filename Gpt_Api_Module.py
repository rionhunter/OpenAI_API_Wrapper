import openai
import time
import logging
from .openai_wrapper import call_openai_method
import datetime

logger = logging.getLogger(__name__)

def use_chat_api(prompt, model, stream, api_key=None):
    start = time.time()
    logger.info("Calling chat API with model %s", model)
    if stream:
        response = call_openai_method(
            "chat.completions.create",
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            api_key=api_key
        )
        print("\nStreaming Response:")
        full_response = ""
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta'].get('content', '')
                print(delta, end='', flush=True)
                full_response += delta
        print()
        logger.info("Duration: %.2fs", time.time() - start)
        return full_response
    else:
        response = call_openai_method(
            "chat.completions.create",
            model=model,
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        usage = getattr(response, 'usage', {})
        logger.info("Duration: %.2fs | Tokens: %s", time.time() - start, usage)
        return response.choices[0].message.content

def use_assistant_api(prompt, assistant_id, api_key=None):
    start = time.time()
    thread = call_openai_method("beta.threads.create", api_key=api_key)
    call_openai_method(
        "beta.threads.messages.create",
        thread_id=thread.id,
        role="user",
        content=prompt,
        api_key=api_key
    )
    run = call_openai_method(
        "beta.threads.runs.create",
        thread_id=thread.id,
        assistant_id=assistant_id,
        api_key=api_key
    )
    while run.status not in ['completed', 'failed']:
        time.sleep(1)
        run = call_openai_method(
            "beta.threads.runs.retrieve",
            thread_id=thread.id,
            run_id=run.id,
            api_key=api_key
        )

    if run.status == 'failed':
        return "Run failed."

    messages = call_openai_method(
        "beta.threads.messages.list",
        thread_id=thread.id,
        api_key=api_key
    )
    logger.info("Duration: %.2fs", time.time() - start)
    return messages.data[0]['content'][0]['text']['value']
