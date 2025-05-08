import openai
import time
from .openai_wrapper import call_openai_method

def use_chat_api(prompt, model, stream):
    if stream:
        response = call_openai_method(
            openai.ChatCompletion.create,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        print("\nStreaming Response:")
        full_response = ""
        for chunk in response:
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0]['delta'].get('content', '')
                print(delta, end='', flush=True)
                full_response += delta
        print()  # New line after streaming ends
        return full_response
    else:
        response = call_openai_method(
            openai.ChatCompletion.create,
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content']

def use_assistant_api(prompt, assistant_id):
    thread = call_openai_method(openai.beta.threads.create)
    call_openai_method(
        openai.beta.threads.messages.create,
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    run = call_openai_method(
        openai.beta.threads.runs.create,
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    while run.status not in ['completed', 'failed']:  # Wait until run completes or fails
        time.sleep(1)
        run = call_openai_method(
            openai.beta.threads.runs.retrieve,
            thread_id=thread.id,
            run_id=run.id
        )

    if run.status == 'failed':
        return "Run failed."

    messages = call_openai_method(openai.beta.threads.messages.list, thread_id=thread.id)
    return messages.data[0]['content'][0]['text']['value']
