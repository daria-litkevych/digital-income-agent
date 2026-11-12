"""Bounded, provider-neutral tool registry and multi-step agent runtime.

The runtime is inert unless explicitly given a live-capable LLM client and an
approved AgentBrain. Tools are injected by the host; there are no implicit
network, filesystem, shell, publishing or billing capabilities.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from agent.brain import AgentBrain, BrainError, ROLE_REGISTRY
from agent.llm import LLMClient, LLMRequest, OfflineMockClient


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], Any]
    required_arguments: tuple[str, ...] = ()
    allowed_arguments: tuple[str, ...] = ()
    requires_approval: bool = False


class ToolRegistry:
    def __init__(self, tools: list[AgentTool] | None = None):
        self._tools: dict[str, AgentTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: AgentTool) -> None:
        if not tool.name or not tool.name.replace("_", "").isalnum():
            raise ValueError("Tool name must be a non-empty identifier.")
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def descriptions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "required_arguments": list(tool.required_arguments),
                "allowed_arguments": list(tool.allowed_arguments),
            }
            for tool in self._tools.values()
        ]

    def invoke(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise BrainError(f"Unknown tool: {name}")
        if tool.requires_approval:
            raise BrainError(f"Tool requires human approval and cannot run autonomously: {name}")
        if not isinstance(arguments, dict):
            raise BrainError("Tool arguments must be a JSON object.")
        missing = set(tool.required_arguments) - set(arguments)
        unexpected = set(arguments) - set(tool.allowed_arguments)
        if missing:
            raise BrainError("Missing tool arguments: " + ", ".join(sorted(missing)))
        if unexpected:
            raise BrainError("Unexpected tool arguments: " + ", ".join(sorted(unexpected)))
        result = tool.handler(arguments)
        # Reject unserialisable or unbounded tool output before it re-enters a prompt.
        try:
            encoded = json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as error:
            raise BrainError("Tool returned non-JSON data.") from error
        if len(encoded) > 20000:
            raise BrainError("Tool output exceeds the 20,000-character limit.")
        return result


class AgentToolRuntime:
    """JSON-protocol tool loop with explicit role, step and approval boundaries."""

    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        *,
        live_approved: bool = False,
        max_steps: int = 4,
        max_output_tokens: int = 900,
    ):
        if max_steps < 1 or max_steps > 8:
            raise ValueError("max_steps must be between 1 and 8")
        if max_output_tokens < 1 or max_output_tokens > 2000:
            raise ValueError("max_output_tokens must be between 1 and 2000")
        self.client = client
        self.registry = registry
        self.live_approved = live_approved
        self.max_steps = max_steps
        self.max_output_tokens = max_output_tokens

    def run(self, role: str, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if role not in ROLE_REGISTRY:
            raise BrainError(f"Unknown specialist role: {role}")
        if not self.live_approved and not isinstance(self.client, OfflineMockClient):
            raise BrainError("Live model client is not approved; refusing tool-runtime invocation.")
        if isinstance(self.client, OfflineMockClient):
            return {
                "status": "blocked",
                "summary": "Offline mock mode cannot execute specialist tool work.",
                "tool_calls": [],
                "execution_mode": "offline_mock",
                "requires_human_approval": True,
            }

        transcript: list[dict[str, Any]] = []
        spec = ROLE_REGISTRY[role]
        for step in range(self.max_steps):
            prompt = {
                "role": role,
                "task": task,
                "context": context,
                "available_tools": self.registry.descriptions(),
                "transcript": transcript,
                "protocol": {
                    "tool_call": {"type": "tool_call", "tool": "registered_name", "arguments": {}},
                    "final": {"type": "final", "result": "the required AgentBrain JSON output object"},
                },
                "rules": [
                    "Use only supplied context and tool observations.",
                    "Never invent sources, prices, quotes, test results or tool observations.",
                    "Only call listed tools and use only their declared arguments.",
                    "Never request publishing, outreach, purchases, billing changes or other side effects.",
                    "When evidence is missing, return needs_evidence rather than guessing.",
                ],
            }
            response = self.client.generate(LLMRequest(
                task=f"{role}:tool-step-{step + 1}:{task[:80]}",
                system=f"You are {spec.name}. Follow the JSON tool protocol exactly.",
                user=json.dumps(prompt, ensure_ascii=False, sort_keys=True),
                max_output_tokens=self.max_output_tokens,
            ))
            if response.is_mock:
                return {
                    "status": "blocked",
                    "summary": "Provider returned a mock response; no tool work was performed.",
                    "tool_calls": transcript,
                    "execution_mode": "offline_mock",
                    "requires_human_approval": True,
                }
            try:
                message = json.loads(response.text)
            except (TypeError, json.JSONDecodeError) as error:
                raise BrainError("Tool runtime response was not valid JSON.") from error
            if not isinstance(message, dict):
                raise BrainError("Tool runtime response must be a JSON object.")
            if message.get("type") == "tool_call":
                tool_name = message.get("tool")
                arguments = message.get("arguments", {})
                observation = self.registry.invoke(tool_name, arguments)
                transcript.append({
                    "step": step + 1, "tool": tool_name,
                    "arguments": arguments, "observation": observation,
                })
                continue
            if message.get("type") == "final":
                result = message.get("result")
                if not isinstance(result, dict):
                    raise BrainError("Final tool-runtime result must be a JSON object.")
                # Reuse AgentBrain's complete contract validator without making
                # another provider request.
                class ReplayClient:
                    def generate(self, request):
                        from agent.llm import LLMResponse
                        return LLMResponse(
                            text=json.dumps(result, ensure_ascii=False),
                            model=response.model, provider=response.provider,
                            input_tokens=0, output_tokens=0,
                            estimated_cost_usd=0.0, is_mock=False,
                        )
                validated = AgentBrain(ReplayClient(), live_approved=True).dispatch(
                    role, task, context
                )
                validated["tool_trace"] = transcript
                validated["tool_steps"] = step + 1
                return validated
            raise BrainError("Tool runtime response type must be tool_call or final.")
        return {
            "status": "needs_evidence",
            "summary": "Tool-step limit reached before a final answer.",
            "tool_trace": transcript,
            "execution_mode": "live",
            "requires_human_approval": True,
        }
