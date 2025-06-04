import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from utils import format_as_json_response

def run_test(api_key=None):
    data = format_as_json_response("hi", "model", "mode")
    assert "\"response\": \"hi\"" in data
    assert "model" in data

if __name__ == "__main__":
    run_test()
