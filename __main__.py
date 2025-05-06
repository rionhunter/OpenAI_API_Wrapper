import argparse
import openai
import sys
import os
import time
import json
from datetime import datetime
from model_manager import confirm_model

# Setup CLI arguments
parser = argparse.ArgumentParser(description='OpenAI GPT API Client')
parser.add_argument('--agent', type=str, required=True, choices=['chat', 'assistant'],
                    help='Choose between "chat" for Chat Completions API or "assistant" for Assistants API')
parser.add_argument('--model', type=str, required=True, help='Specify the OpenAI model to use')
parser.add_argument('--prompt', type=str, help='Prompt to send to the model')
parser.add_argument('--prompt_file', type=str, help='File path to a prompt text file')
parser.add_argument('--stream', action='store_true', help='Enable streaming output (chat API only)')
parser.add_argument('--assistant_id', type=str, help='Required if using agent type "assistant"')
parser.add_argument('--output_file', type=str, help='Optional file path to save the model response')
parser.add_argument('--json_output', action='store_true', help='Output result as JSON')
parser.add_argument('--api_key', type=str, help='OpenAI API Key')
args = parser.parse_args()

# Confirm model exists via manager
if not confirm_model(args.model):
    print(f"Error: Model '{args.model}' not recognized by OpenAI.", file=sys.stderr)
    sys.exit(1)

openai.api_key = args.api_key if args.api_key else os.getenv("OPENAI_API_KEY")

# Load prompt from file if provided
if args.prompt_file:
    with open(args.prompt_file, 'r') as file:
        prompt = file.read()
elif args.prompt:
    prompt = args.prompt
else:
    print("Error: Must provide either --prompt or --prompt_file", file=sys.stderr)
    sys.exit(1)

# --- Chat Completion Endpoint ---
def use_chat_api(prompt, model, stream):
    if stream:
        response = openai.ChatCompletion.create(
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
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content']

# --- Assistants API Endpoint ---
def use_assistant_api(prompt, assistant_id):
    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    while run.status not in ['completed', 'failed']:  # Wait until run completes or fails
        time.sleep(1)
        run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status == 'failed':
        return "Run failed."

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0]['content'][0]['text']['value']

# --- Main Execution ---
if args.agent == 'chat':
    result = use_chat_api(prompt, args.model, args.stream)
elif args.agent == 'assistant':
    if not args.assistant_id:
        print("Error: --assistant_id is required for agent type 'assistant'", file=sys.stderr)
        sys.exit(1)
    result = use_assistant_api(prompt, args.assistant_id)

# Format response
if args.json_output:
    metadata = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": args.agent,
        "model": args.model,
        "response": result
    }
    output = json.dumps(metadata, indent=2)
else:
    output = result

print("\nModel Response:\n", output)

# Optionally save result to file
if args.output_file and result:
    with open(args.output_file, 'w') as f:
        f.write(output)
    print(f"\nResponse saved to {args.output_file}")
