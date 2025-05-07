import argparse
import os
import openai
from model_manager import confirm_model
from Gpt_Api_Module import use_chat_api, use_assistant_api
from Dalle_Api_Module import generate_dalle_image
from Whisper_Api_Module import transcribe_audio

# --- CLI Entry ---
parser = argparse.ArgumentParser(description='Unified OpenAI CLI')
parser.add_argument('mode', choices=['gpt', 'dalle', 'whisper'], help='Operation mode')
parser.add_argument('--model', type=str, required=True, help='Model to use')
parser.add_argument('--prompt', type=str, help='Text prompt')
parser.add_argument('--prompt_file', type=str, help='Path to prompt text file')
parser.add_argument('--stream', action='store_true', help='Stream GPT response')
parser.add_argument('--assistant_id', type=str, help='Assistant ID for GPT assistant mode')
parser.add_argument('--file', type=str, help='Path to audio file for Whisper')
parser.add_argument('--translate', action='store_true', help='Translate to English (Whisper)')
parser.add_argument('--language', type=str, help='Language hint (Whisper)')
parser.add_argument('--format', type=str, default='json', help='Output format (Whisper)')
parser.add_argument('--size', type=str, default='1024x1024', help='Image size (DALL·E)')
parser.add_argument('--quality', type=str, default='standard', help='Image quality (DALL·E 3)')
parser.add_argument('--style', type=str, help='Image style (DALL·E 3)')
parser.add_argument('--n', type=int, default=1, help='Number of images (DALL·E)')
parser.add_argument('--output_file', type=str, help='Output file path')
parser.add_argument('--output_dir', type=str, default='images', help='Output directory (DALL·E)')
parser.add_argument('--json_output', action='store_true', help='Format GPT result as JSON')
parser.add_argument('--api_key', type=str, help='OpenAI API key')
args = parser.parse_args()

openai.api_key = args.api_key if args.api_key else os.getenv("OPENAI_API_KEY")

if not confirm_model(args.model):
    print(f"Model '{args.model}' is not recognized by OpenAI.")
    exit(1)

if args.prompt_file:
    with open(args.prompt_file, 'r') as f:
        args.prompt = f.read()

if args.mode == 'gpt':
    if args.assistant_id:
        result = use_assistant_api(args.prompt, args.assistant_id)
    else:
        result = use_chat_api(args.prompt, args.model, args.stream)
    if args.json_output:
        import json
        from datetime import datetime
        result = json.dumps({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": args.model,
            "mode": args.mode,
            "response": result
        }, indent=2)
    print(result)
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(result)

elif args.mode == 'dalle':
    generate_dalle_image(args)

elif args.mode == 'whisper':
    if not args.file:
        raise ValueError("Whisper mode requires --file parameter")
    transcribe_audio(args)
