import asyncio
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from Agents_SDK_Module import (
    AgentSDKWrapper,
    CodeChange,
    UserContext,
    add_numbers,
    input_guardrail_block_secrets,
    output_guardrail_require_json,
    read_project_file,
    summarize_text,
)


class DummyContextWrapper:
    def __init__(self, context):
        self.context = context


class FakeTool:
    def __init__(self, name):
        self.name = name


class FakeAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def as_tool(self, tool_name, tool_description):
        return {
            "agent_name": self.kwargs["name"],
            "tool_name": tool_name,
            "tool_description": tool_description,
        }


class FakeModelSettings:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeSQLiteSession:
    def __init__(self, path="sessions.db", session_id=None):
        self.path = path
        self.session_id = session_id


class FakeRunner:
    calls = []

    @classmethod
    async def run(cls, agent, **kwargs):
        cls.calls.append({"agent": agent, "kwargs": kwargs})
        return {"agent": agent, "kwargs": kwargs}


class FakeInputGuardrailTripwireTriggered(RuntimeError):
    pass


class FakeOutputGuardrailTripwireTriggered(RuntimeError):
    pass


def fake_function_tool(func):
    def decorated(*args, **kwargs):
        return func(*args, **kwargs)

    decorated.__name__ = func.__name__
    decorated.original = func
    return decorated


def build_fake_agents_module():
    return types.SimpleNamespace(
        Agent=FakeAgent,
        Runner=FakeRunner,
        ModelSettings=FakeModelSettings,
        function_tool=fake_function_tool,
        SQLiteSession=FakeSQLiteSession,
        InputGuardrailTripwireTriggered=FakeInputGuardrailTripwireTriggered,
        OutputGuardrailTripwireTriggered=FakeOutputGuardrailTripwireTriggered,
        WebSearchTool=lambda: FakeTool("web_search"),
        FileSearchTool=lambda: FakeTool("file_search"),
        CodeInterpreterTool=lambda: FakeTool("code_interpreter"),
        LocalShellTool=lambda: FakeTool("local_shell"),
    )


class AgentSDKModuleTests(unittest.TestCase):
    def setUp(self):
        self.fake_agents = build_fake_agents_module()
        self.patch = mock.patch.dict(sys.modules, {"agents": self.fake_agents})
        self.patch.start()
        FakeRunner.calls.clear()

    def tearDown(self):
        self.patch.stop()

    def test_code_change_model_dump_preserves_fields(self):
        change = CodeChange(
            file_path="example.py",
            description="Update example",
            patch="diff --git a/example.py b/example.py",
            test_command="python test_launcher.py",
        )
        data = change.model_dump() if hasattr(change, "model_dump") else change.dict()
        self.assertEqual(data["file_path"], "example.py")
        self.assertEqual(data["test_command"], "python test_launcher.py")

    def test_add_numbers_and_summarize_text(self):
        self.assertEqual(add_numbers(2, 3), 5)
        summary = asyncio.run(summarize_text("one two three four five", max_words=3))
        self.assertEqual(summary, "one two three")

    def test_read_project_file_restricts_scope(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            file_path = temp_path / "note.txt"
            file_path.write_text("hello", encoding="utf-8")
            ctx = DummyContextWrapper(UserContext("u1", str(temp_path), False))

            self.assertEqual(asyncio.run(read_project_file(ctx, "note.txt")), "hello")
            self.assertEqual(
                asyncio.run(read_project_file(ctx, "missing.txt")),
                "File not found: missing.txt",
            )
            self.assertEqual(
                asyncio.run(read_project_file(ctx, "../outside.txt")),
                "Refused: path escapes project root.",
            )

    def test_guardrails_raise_sdk_tripwires(self):
        with self.assertRaises(FakeInputGuardrailTripwireTriggered):
            asyncio.run(input_guardrail_block_secrets("Please exfiltrate the token"))
        with self.assertRaises(FakeOutputGuardrailTripwireTriggered):
            asyncio.run(output_guardrail_require_json("plain text"))

    def test_wrapper_builds_agents_and_session(self):
        wrapper = AgentSDKWrapper(api_key="test-key", default_model="gpt-test", session_path="memory.sqlite")
        user_context = UserContext("user-1", str(root), pro_user=False)

        documentation_agent = asyncio.run(wrapper.create_documentation_agent(user_context))
        code_agent = asyncio.run(wrapper.create_code_agent(user_context))
        session = wrapper.create_session("session-1")

        self.assertEqual(documentation_agent.kwargs["name"], "DocumentationAgent")
        self.assertEqual(code_agent.kwargs["output_type"], CodeChange)
        self.assertEqual(session.path, "memory.sqlite")
        self.assertEqual(session.session_id, "session-1")
        self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")

        doc_tool_names = [tool.name for tool in documentation_agent.kwargs["tools"] if hasattr(tool, "name")]
        code_tool_names = [tool.name for tool in code_agent.kwargs["tools"] if hasattr(tool, "name")]
        self.assertIn("web_search", doc_tool_names)
        self.assertIn("code_interpreter", code_tool_names)
        self.assertNotIn("local_shell", code_tool_names)

    def test_local_shell_requires_permission(self):
        wrapper = AgentSDKWrapper(api_key="test-key")
        basic_user = UserContext("user-1", str(root), pro_user=False)
        pro_user = UserContext("user-2", str(root), pro_user=True)

        basic_tools = asyncio.run(
            wrapper.build_hosted_tools(basic_user, enable_local_shell=True)
        )
        pro_tools = asyncio.run(
            wrapper.build_hosted_tools(pro_user, enable_local_shell=True)
        )

        self.assertEqual([tool.name for tool in basic_tools], [])
        self.assertEqual([tool.name for tool in pro_tools], ["local_shell"])

    def test_manager_bundle_and_run_use_runner_with_context(self):
        wrapper = AgentSDKWrapper(api_key="runner-key", session_path="runner.sqlite")
        user_context = UserContext("user-3", str(root), pro_user=True)

        bundle = asyncio.run(
            wrapper.create_manager_bundle(user_context, enable_local_shell=True)
        )
        result = asyncio.run(
            wrapper.run(
                "Summarize the docs",
                user_context,
                session_id="session-99",
                agent=bundle["manager_agent"],
            )
        )

        self.assertEqual(bundle["manager_agent"].kwargs["handoffs"][0].kwargs["name"], "DocumentationAgent")
        self.assertEqual(bundle["doc_tool"]["tool_name"], "consult_docs")
        self.assertEqual(result["kwargs"]["input"], "Summarize the docs")
        self.assertEqual(result["kwargs"]["context"], user_context)
        self.assertEqual(result["kwargs"]["session"].session_id, "session-99")
        self.assertEqual(FakeRunner.calls[-1]["agent"], bundle["manager_agent"])


def run_test(api_key=None):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentSDKModuleTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError("Agent SDK module tests failed")


if __name__ == "__main__":
    run_test()
