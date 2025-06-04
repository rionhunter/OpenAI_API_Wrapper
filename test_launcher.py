import argparse
import importlib
import pathlib
import sys


def main():
    parser = argparse.ArgumentParser(description="Run all test scripts")
    parser.add_argument("--api_key", help="OpenAI API key", default=None)
    args = parser.parse_args()

    # Ensure project root is on the path
    root = pathlib.Path(__file__).parent
    sys.path.insert(0, str(root.parent))

    test_dir = pathlib.Path(__file__).parent / "tests"
    failures = 0
    for path in sorted(test_dir.glob("test_*.py")):
        mod_name = f"tests.{path.stem}"
        module = importlib.import_module(mod_name)
        test_func = getattr(module, "run_test", None)
        if not test_func:
            print(f"{path.name}: no run_test function")
            continue
        try:
            test_func(args.api_key)
            print(f"{path.name}: PASS")
        except Exception as e:
            failures += 1
            print(f"{path.name}: FAIL - {e}")
    if failures:
        sys.exit(f"{failures} test(s) failed")


if __name__ == "__main__":
    main()
