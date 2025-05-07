import subprocess
import os
from datetime import datetime

results = {}
log_base = ".demo_log"
log_ext = ".txt"

# Rotate up to 5 logs
for i in range(4, -1, -1):
    src = f"{log_base}{'' if i == 0 else f'.{i}'}{log_ext}"
    dst = f"{log_base}.{i+1}{log_ext}"
    if os.path.exists(src):
        if i == 4:
            os.remove(src)
        else:
            os.rename(src, dst)

log_path = f"{log_base}{log_ext}"


def log_line(log, message):
    timestamp = datetime.utcnow().isoformat() + "Z"
    log_entry = f"[{timestamp}] {message}"
    log.write(log_entry + "\n")
    print(log_entry)


def run_demo(name, args):
    print(f"\nRunning {name} Demo...")
    try:
        with open(log_path, 'a') as log:
            log_line(log, f"{name.upper()} DEMO START")
            process = subprocess.Popen(
                ["python", "main.py", *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                log_line(log, line.rstrip())
            return_code = process.wait()
            results[name] = 'Success' if return_code == 0 else f'Failed (code {return_code})'
    except Exception as e:
        results[name] = f"Error: {e}"


run_demo("gpt", [
    "gpt",
    "--model", "gpt-3.5-turbo",
    "--prompt", "Tell me a joke about penguins.",
    "--json_output"
])

run_demo("dalle", [
    "dalle",
    "--model", "dall-e-2",
    "--prompt", "An astronaut lounging in a tropical resort in space",
    "--output_dir", "demo_images"
])

run_demo("whisper", [
    "whisper",
    "--model", "whisper-1",
    "--file", "sample_audio.mp3",
    "--format", "text"
])

print("\nDEMO SUMMARY:")
for mode, status in results.items():
    print(f"- {mode.upper()}: {status}")
