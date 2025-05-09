import argparse
import openai
import os
import json
import time
from datetime import datetime
from model_manager import confirm_model
from openai_wrapper import call_openai_method

# --- CLI Setup ---
parser = argparse.ArgumentParser(description='OpenAI Whisper Transcription Tool')
parser.add_argument('--model', type=str, required=True, help='Model ID (e.g., whisper-1)')
parser.add_argument('--file', type=str, required=True, help='Path to audio file to transcribe')
parser.add_argument('--language', type=str, help='Optional language code (e.g., en, es, fr)')
parser.add_argument('--translate', action='store_true', help='Translate to English instead of transcribing')
parser.add_argument('--format', type=str, choices=['json', 'text', 'srt', 'vtt', 'verbose_json'], default='json', help='Output format')
parser.add_argument('--output_file', type=str, help='File to save the result')
parser.add_argument('--api_key', type=str, help='OpenAI API key')
args = parser.parse_args()

api_key = args.api_key if args.api_key else os.getenv("OPENAI_API_KEY")

# --- Model Check ---
if not confirm_model(args.model):
    print(f"Error: Model '{args.model}' is not recognized by OpenAI.")
    exit(1)

# --- Transcription / Translation ---
operation = "translate" if args.translate else "transcribe"
method = getattr(openai.Audio, operation)

start = time.time()
with open(args.file, 'rb') as audio_file:
    transcript = call_openai_method(
        method,
        model=args.model,
        file=audio_file,
        language=args.language,
        response_format=args.format,
        api_key=api_key
    )

# --- Output ---
if isinstance(transcript, dict):
    output = json.dumps(transcript, indent=2)
else:
    output = transcript

print(f"Duration: {time.time() - start:.2f}s")

if args.output_file:
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"Transcription saved to {args.output_file}")
else:
    print("\nTranscription Output:\n")
    print(output)
