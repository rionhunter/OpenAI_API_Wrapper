import argparse
import openai
import os
import json
import time
import logging
from datetime import datetime
from .model_manager import confirm_model
from .openai_wrapper import call_openai_method

logger = logging.getLogger(__name__)

def transcribe_audio(args):
    api_key = args.api_key if args.api_key else os.getenv("OPENAI_API_KEY")

    if not confirm_model(args.model):
        logger.error("Model '%s' is not recognized by OpenAI.", args.model)
        exit(1)

    operation = "translate" if args.translate else "transcribe"
    method = f"audio.{operation}s.create"

    start = time.time()
    logger.info("Starting %s with model %s", operation, args.model)
    with open(args.file, 'rb') as audio_file:
        transcript = call_openai_method(
            method,
            model=args.model,
            file=audio_file,
            language=args.language,
            response_format=args.format,
            api_key=api_key
        )

    if isinstance(transcript, dict):
        output = json.dumps(transcript, indent=2)
    else:
        output = transcript

    logger.info("Duration: %.2fs", time.time() - start)

    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info("Transcription saved to %s", args.output_file)
    else:
        print("\nTranscription Output:\n")
        print(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OpenAI Whisper Transcription Tool')
    parser.add_argument('--model', type=str, required=True, help='Model ID (e.g., whisper-1)')
    parser.add_argument('--file', type=str, required=True, help='Path to audio file to transcribe')
    parser.add_argument('--language', type=str, help='Optional language code (e.g., en, es, fr)')
    parser.add_argument('--translate', action='store_true', help='Translate to English instead of transcribing')
    parser.add_argument('--format', type=str, choices=['json', 'text', 'srt', 'vtt', 'verbose_json'], default='json', help='Output format')
    parser.add_argument('--output_file', type=str, help='File to save the result')
    parser.add_argument('--api_key', type=str, help='OpenAI API key')
    args = parser.parse_args()
    transcribe_audio(args)
