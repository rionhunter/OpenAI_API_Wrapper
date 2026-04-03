import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class TaskStore:
    """Simple task store that can be persisted across runs."""

    def __init__(self, tasks: list[dict[str, Any]] | None = None):
        self.tasks = tasks or []

    @classmethod
    def from_file(cls, path: str) -> "TaskStore":
        if not path or not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
        return cls(tasks=tasks)

    def save(self, path: str) -> None:
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"tasks": self.tasks}, f, indent=2)

    def _next_id(self) -> int:
        return (max((int(t.get("id", 0)) for t in self.tasks), default=0) + 1)

    def create_task(self, title: str, details: str = "") -> dict[str, Any]:
        task = {
            "id": self._next_id(),
            "title": title.strip(),
            "details": details.strip(),
            "status": "open",
        }
        self.tasks.append(task)
        return task

    def list_tasks(self, status: str = "all") -> list[dict[str, Any]]:
        if status == "all":
            return list(self.tasks)
        return [task for task in self.tasks if task.get("status") == status]

    def complete_task(self, task_id: int) -> dict[str, Any] | None:
        for task in self.tasks:
            if int(task.get("id", -1)) == int(task_id):
                task["status"] = "completed"
                return task
        return None


def _load_agents_sdk():
    try:
        from agents import Agent, Runner, function_tool

        return Agent, Runner, function_tool
    except Exception as exc:  # pragma: no cover - exercised in environments without SDK
        raise RuntimeError(
            "OpenAI Agent SDK is required for agent mode. Install with `pip install openai-agents`."
        ) from exc


def run_agent_sdk_pipeline(
    prompt: str,
    model: str,
    api_key: str | None = None,
    instructions: str | None = None,
    task_state_file: str | None = None,
) -> str:
    """
    Alternative pipeline that instantiates an OpenAI Agent SDK agent with function tools
    and an ongoing task store persisted between runs.
    """
    if not prompt:
        raise ValueError("A prompt is required for agent mode.")

    Agent, Runner, function_tool = _load_agents_sdk()
    task_store = TaskStore.from_file(task_state_file) if task_state_file else TaskStore()

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    @function_tool
    def create_task(title: str, details: str = "") -> str:
        """Create a new task in the ongoing task store."""
        task = task_store.create_task(title=title, details=details)
        return json.dumps(task)

    @function_tool
    def list_tasks(status: str = "all") -> str:
        """List tasks by status: all | open | completed."""
        return json.dumps(task_store.list_tasks(status=status))

    @function_tool
    def complete_task(task_id: int) -> str:
        """Mark a task as completed by numeric task id."""
        task = task_store.complete_task(task_id=task_id)
        return json.dumps(task if task else {"error": "Task not found"})

    agent_instructions = instructions or (
        "You are a task-oriented OpenAI agent. "
        "Use function tools to create, track, and complete ongoing tasks. "
        "When helpful, call list_tasks before deciding next actions."
    )

    agent = Agent(
        name="OpenAIWrapperAgentPipeline",
        instructions=agent_instructions,
        model=model,
        tools=[create_task, list_tasks, complete_task],
    )

    result = Runner.run_sync(agent, prompt)
    output = getattr(result, "final_output", None)
    if output is None:
        output = str(result)

    if task_state_file:
        task_store.save(task_state_file)
        logger.info("Saved ongoing task state to %s", task_state_file)

    return output
