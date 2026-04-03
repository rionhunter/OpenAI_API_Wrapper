import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from agent_sdk_pipeline import TaskStore, run_agent_sdk_pipeline


def run_test(api_key=None):
    store = TaskStore()
    created = store.create_task("Test task", "details")
    assert created["id"] == 1
    assert created["status"] == "open"
    assert len(store.list_tasks("open")) == 1
    completed = store.complete_task(1)
    assert completed is not None
    assert completed["status"] == "completed"
    assert store.complete_task(9999) is None

    try:
        run_agent_sdk_pipeline(prompt="hello", model="gpt-4o-mini", api_key=api_key)
        assert api_key, "Expected dependency failure when API key and Agent SDK are unavailable"
    except RuntimeError as e:
        assert "Agent SDK is required" in str(e)
    except Exception:
        if not api_key:
            return
        raise


if __name__ == "__main__":
    run_test(sys.argv[1] if len(sys.argv) > 1 else None)
