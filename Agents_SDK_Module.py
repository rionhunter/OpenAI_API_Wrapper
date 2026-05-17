from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Any, Optional


class _FallbackInputGuardrailTripwireTriggered(RuntimeError):
    """Fallback used when the Agents SDK is unavailable."""


class _FallbackOutputGuardrailTripwireTriggered(RuntimeError):
    """Fallback used when the Agents SDK is unavailable."""


try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        """Minimal fallback that preserves constructor behaviour used in tests."""

        def __init__(self, **data):
            annotations = getattr(self, "__annotations__", {})
            missing = [
                name for name, value in self.__class__.__dict__.items()
                if value is ... and name not in data
            ]
            if missing:
                raise TypeError(f"Missing required fields: {', '.join(sorted(missing))}")
            for field_name in annotations:
                if field_name in data:
                    setattr(self, field_name, data[field_name])
                elif hasattr(self.__class__, field_name):
                    default_value = getattr(self.__class__, field_name)
                    setattr(self, field_name, None if default_value is ... else default_value)
                else:
                    setattr(self, field_name, None)

        def model_dump(self):
            return {
                field_name: getattr(self, field_name)
                for field_name in getattr(self, "__annotations__", {})
            }

    def Field(default=..., description=""):
        return default


def _load_agents_sdk():
    try:
        from agents import (
            Agent,
            Runner,
            ModelSettings,
            function_tool,
            SQLiteSession,
            InputGuardrailTripwireTriggered,
            OutputGuardrailTripwireTriggered,
            WebSearchTool,
            FileSearchTool,
            CodeInterpreterTool,
            LocalShellTool,
        )
    except ImportError as exc:
        raise ImportError(
            "The Agents SDK wrapper requires `openai-agents`. Install it with "
            "`pip install openai-agents pydantic`."
        ) from exc

    return {
        "Agent": Agent,
        "Runner": Runner,
        "ModelSettings": ModelSettings,
        "function_tool": function_tool,
        "SQLiteSession": SQLiteSession,
        "InputGuardrailTripwireTriggered": InputGuardrailTripwireTriggered,
        "OutputGuardrailTripwireTriggered": OutputGuardrailTripwireTriggered,
        "WebSearchTool": WebSearchTool,
        "FileSearchTool": FileSearchTool,
        "CodeInterpreterTool": CodeInterpreterTool,
        "LocalShellTool": LocalShellTool,
    }


def _get_tripwire_exceptions():
    try:
        sdk = _load_agents_sdk()
        return (
            sdk["InputGuardrailTripwireTriggered"],
            sdk["OutputGuardrailTripwireTriggered"],
        )
    except ImportError:
        return (
            _FallbackInputGuardrailTripwireTriggered,
            _FallbackOutputGuardrailTripwireTriggered,
        )


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


@dataclass
class UserContext:
    user_id: str
    project_root: str
    pro_user: bool = False

    async def allow_risky_shell(self) -> bool:
        return self.pro_user


class CodeChange(BaseModel):
    file_path: str = Field(..., description="Relative path to the file to modify")
    description: str = Field(..., description="Human-readable summary of the change")
    patch: str = Field(..., description="Unified diff patch (or raw text to append)")
    test_command: Optional[str] = Field(
        None,
        description="Command to run tests that validate the change",
    )


def add_numbers(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


async def summarize_text(text: str, max_words: int = 50) -> str:
    """Summarize the given text in <= max_words words."""
    words = text.split()
    return " ".join(words[:max_words])


async def read_project_file(ctx: Any, rel_path: str) -> str:
    """Read a file from the project root stored in the run context."""
    user_ctx: UserContext = ctx.context
    full_path = os.path.abspath(os.path.normpath(os.path.join(user_ctx.project_root, rel_path)))
    project_root = os.path.abspath(user_ctx.project_root)
    if os.path.commonpath([project_root, full_path]) != project_root:
        return "Refused: path escapes project root."
    try:
        with open(full_path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        return f"File not found: {rel_path}"


async def input_guardrail_block_secrets(user_input: str) -> None:
    lower = (user_input or "").lower()
    if "steal my env" in lower or "exfiltrate" in lower:
        exception_class, _ = _get_tripwire_exceptions()
        raise exception_class("Request blocked by input guardrail.")


async def output_guardrail_require_json(result_text: str) -> None:
    if "{" not in result_text or "}" not in result_text:
        _, exception_class = _get_tripwire_exceptions()
        raise exception_class("Expected JSON-like structured output.")


class AgentSDKWrapper:
    """Small wrapper around the OpenAI Agents SDK with safe defaults."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4.1-mini",
        session_path: str = "sessions.db",
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.session_path = session_path

    def configure_api_key(self) -> str:
        os.environ["OPENAI_API_KEY"] = self.api_key
        return self.api_key

    def create_session(self, session_id: Optional[str] = None):
        sdk = _load_agents_sdk()
        self.configure_api_key()
        return sdk["SQLiteSession"](path=self.session_path, session_id=session_id)

    def _decorate_function_tools(self):
        sdk = _load_agents_sdk()
        decorate = sdk["function_tool"]
        return {
            "add_numbers": decorate(add_numbers),
            "summarize_text": decorate(summarize_text),
            "read_project_file": decorate(read_project_file),
        }

    async def build_hosted_tools(
        self,
        user_context: Optional[UserContext] = None,
        *,
        enable_web_search: bool = False,
        enable_file_search: bool = False,
        enable_code_interpreter: bool = False,
        enable_local_shell: bool = False,
    ):
        sdk = _load_agents_sdk()
        tools = []
        if enable_web_search:
            tools.append(sdk["WebSearchTool"]())
        if enable_file_search:
            tools.append(sdk["FileSearchTool"]())
        if enable_code_interpreter:
            tools.append(sdk["CodeInterpreterTool"]())
        if enable_local_shell:
            allow_local_shell = True
            if user_context is not None and hasattr(user_context, "allow_risky_shell"):
                allow_local_shell = bool(await _maybe_await(user_context.allow_risky_shell()))
            if allow_local_shell:
                tools.append(sdk["LocalShellTool"]())
        return tools

    def build_model_settings(self, temperature: float = 0.2, **kwargs):
        sdk = _load_agents_sdk()
        return sdk["ModelSettings"](temperature=temperature, **kwargs)

    async def create_documentation_agent(
        self,
        user_context: Optional[UserContext] = None,
        *,
        model: Optional[str] = None,
        enable_web_search: bool = True,
        enable_file_search: bool = False,
    ):
        sdk = _load_agents_sdk()
        self.configure_api_key()
        tools = self._decorate_function_tools()
        hosted_tools = await self.build_hosted_tools(
            user_context,
            enable_web_search=enable_web_search,
            enable_file_search=enable_file_search,
        )
        return sdk["Agent"](
            name="DocumentationAgent",
            instructions=(
                "You are a concise technical writer. If asked about project files, "
                "use read_project_file. If asked about general facts, you may use web search."
            ),
            tools=[tools["read_project_file"], *hosted_tools],
            model=model or self.default_model,
            model_settings=self.build_model_settings(temperature=0.2),
        )

    async def create_code_agent(
        self,
        user_context: Optional[UserContext] = None,
        *,
        model: Optional[str] = None,
        enable_code_interpreter: bool = True,
        enable_local_shell: bool = False,
    ):
        sdk = _load_agents_sdk()
        self.configure_api_key()
        tools = self._decorate_function_tools()
        hosted_tools = await self.build_hosted_tools(
            user_context,
            enable_code_interpreter=enable_code_interpreter,
            enable_local_shell=enable_local_shell,
        )
        return sdk["Agent"](
            name="CodeAgent",
            instructions=(
                "You are a senior software engineer. Produce CodeChange objects "
                "describing minimal, safe edits."
            ),
            tools=[
                tools["add_numbers"],
                tools["summarize_text"],
                *hosted_tools,
            ],
            output_type=CodeChange,
            model=model or self.default_model,
            model_settings=self.build_model_settings(temperature=0.1),
        )

    async def create_manager_bundle(
        self,
        user_context: Optional[UserContext] = None,
        *,
        model: Optional[str] = None,
        enable_web_search: bool = True,
        enable_file_search: bool = False,
        enable_code_interpreter: bool = True,
        enable_local_shell: bool = False,
    ):
        sdk = _load_agents_sdk()
        documentation_agent = await self.create_documentation_agent(
            user_context,
            model=model,
            enable_web_search=enable_web_search,
            enable_file_search=enable_file_search,
        )
        code_agent = await self.create_code_agent(
            user_context,
            model=model,
            enable_code_interpreter=enable_code_interpreter,
            enable_local_shell=enable_local_shell,
        )
        doc_tool = documentation_agent.as_tool(
            tool_name="consult_docs",
            tool_description="Consult project files or the web for authoritative info.",
        )
        code_tool = code_agent.as_tool(
            tool_name="propose_code_change",
            tool_description="Propose a concrete CodeChange with validation guidance.",
        )
        manager_agent = sdk["Agent"](
            name="ManagerAgent",
            instructions=(
                "Coordinate documentation lookups, code-change planning, and handoffs. "
                "Prefer tool use for bounded tasks and transfer when deeper work is needed."
            ),
            tools=[doc_tool, code_tool],
            handoffs=[documentation_agent, code_agent],
            model=model or self.default_model,
            model_settings=self.build_model_settings(temperature=0.1),
        )
        return {
            "documentation_agent": documentation_agent,
            "code_agent": code_agent,
            "doc_tool": doc_tool,
            "code_tool": code_tool,
            "manager_agent": manager_agent,
        }

    async def run(
        self,
        prompt: str,
        user_context: Optional[UserContext] = None,
        *,
        session_id: Optional[str] = None,
        agent=None,
    ):
        sdk = _load_agents_sdk()
        self.configure_api_key()
        target_agent = agent
        if target_agent is None:
            bundle = await self.create_manager_bundle(user_context)
            target_agent = bundle["manager_agent"]

        runner_kwargs = {"input": prompt}
        if user_context is not None:
            runner_kwargs["context"] = user_context
        if session_id is not None:
            runner_kwargs["session"] = self.create_session(session_id)
        return await sdk["Runner"].run(target_agent, **runner_kwargs)
