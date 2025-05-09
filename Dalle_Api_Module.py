import argparse
import openai
import os
import json
import time
from datetime import datetime
from model_manager import confirm_model
from openai_wrapper import call_openai_method

# --- CLI Setup ---
parser = argparse.ArgumentParser(description='OpenAI DALL·E Image Generator')
parser.add_argument('--model', type=str, required=True, help='Model ID (e.g., dall-e-3 or dall-e-2)')
parser.add_argument('--prompt', type=str, required=True, help='Text prompt to generate an image')
parser.add_argument('--size', type=str, choices=['256x256', '512x512', '1024x1024'], default='1024x1024', help='Image resolution')
parser.add_argument('--quality', type=str, choices=['standard', 'hd'], default='standard', help='Image quality (DALL·E 3 only)')
parser.add_argument('--style', type=str, choices=['vivid', 'natural'], help='Optional style parameter (DALL·E 3 only)')
parser.add_argument('--n', type=int, default=1, help='Number of images to generate')
parser.add_argument('--output_dir', type=str, default='images', help='Directory to save generated images')
parser.add_argument('--api_key', type=str, help='OpenAI API key')
args = parser.parse_args()

api_key = args.api_key if args.api_key else os.getenv("OPENAI_API_KEY")

# --- Model Check ---
if not confirm_model(args.model):
    print(f"Error: Model '{args.model}' is not recognized by OpenAI.")
    exit(1)

# --- Request Preparation ---
request_payload = {
    "model": args.model,
    "prompt": args.prompt,
    "size": args.size,
    "n": args.n,
    "response_format": "url",
    "api_key": api_key
}

if args.model == "dall-e-3":
    request_payload["quality"] = args.quality
    if args.style:
        request_payload["style"] = args.style

# --- Request Execution ---
start = time.time()
response = call_openai_method(openai.Image.create, **request_payload)
print(f"Duration: {time.time() - start:.2f}s")

# --- Output Handling ---
os.makedirs(args.output_dir, exist_ok=True)
timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

for i, item in enumerate(response["data"]):
    image_url = item["url"]
    filename = f"{args.output_dir}/dalle_{timestamp}_{i+1}.json"
    with open(filename, 'w') as f:
        json.dump({"url": image_url, "prompt": args.prompt}, f, indent=2)
    print(f"Saved URL to {filename}: {image_url}")
