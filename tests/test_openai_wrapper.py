import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

try:
    from openai_wrapper import generate_content
except Exception:
    generate_content = None


def run_test(api_key=None):
    if generate_content is None:
        print("openai not installed; skipping live API test.")
        return
    if not api_key:
        print("No API key provided; skipping live API test.")
        return
    result = generate_content("Say hello", api_key, model="gpt-3.5-turbo")
    assert isinstance(result, str) and result

if __name__ == "__main__":
    import sys
    run_test(sys.argv[1] if len(sys.argv) > 1 else None)
