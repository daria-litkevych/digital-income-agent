"""Explicitly gated composition root for live autonomous studio execution.

No environment variable or repository default enables paid inference. The host
must pass an explicit approval flag after a user-approved provider, spend cap
and credential setup. Merely constructing the factory performs no network call.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agent.llm import LLMSettings, OpenAICompatibleClient
from agent.orchestrator import MultiAgentOrchestrator
from agent.research_tools import build_research_tool_registry
from agent.spend_ledger import SpendLedger
from agent.tool_runtime import AgentToolRuntime, ToolRegistry
from agent.workspace_tools import ProposalWorkspace, build_workspace_tool_registry


class LiveStudioApprovalError(RuntimeError):
    pass


@dataclass
class LiveStudio:
    orchestrator: MultiAgentOrchestrator
    workspace: ProposalWorkspace

    def close(self) -> None:
        self.workspace.close()


def _required(env: dict[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise LiveStudioApprovalError(f"Missing required runtime setting: {key}")
    return value


def build_live_studio(
    repository_root: str | Path,
    *,
    checkpoint_loader: Callable[[], dict[str, Any]],
    checkpoint_saver: Callable[[dict[str, Any]], None],
    approval_confirmed: bool = False,
    env: dict[str, str] | None = None,
) -> LiveStudio:
    """Build a live runtime only after a separate, explicit host approval.

    The scheduled workflow does not call this factory. It is a composition
    boundary for a future, explicitly approved run; no credentials are stored
    in source and no provider call occurs during construction.
    """
    if approval_confirmed is not True:
        raise LiveStudioApprovalError("Human approval is required before live studio construction.")
    values = dict(os.environ if env is None else env)
    if values.get("STUDIO_LIVE_ENABLED", "").lower() != "true":
        raise LiveStudioApprovalError("STUDIO_LIVE_ENABLED is not explicitly true.")
    api_key = _required(values, "STUDIO_LLM_API_KEY")
    settings = LLMSettings(
        enabled=True,
        provider=_required(values, "STUDIO_LLM_PROVIDER"),
        base_url=_required(values, "STUDIO_LLM_BASE_URL"),
        model=_required(values, "STUDIO_LLM_MODEL"),
        max_output_tokens=int(values.get("STUDIO_LLM_MAX_OUTPUT_TOKENS", "900")),
        max_input_characters=int(values.get("STUDIO_LLM_MAX_INPUT_CHARACTERS", "12000")),
        max_cost_per_call_usd=float(_required(values, "STUDIO_LLM_MAX_COST_PER_CALL_USD")),
        input_price_per_million_usd=float(_required(values, "STUDIO_LLM_INPUT_PRICE_PER_MILLION_USD")),
        output_price_per_million_usd=float(_required(values, "STUDIO_LLM_OUTPUT_PRICE_PER_MILLION_USD")),
        timeout_seconds=int(values.get("STUDIO_LLM_TIMEOUT_SECONDS", "30")),
    )
    settings.validate_for_live_use()
    monthly_cap = float(_required(values, "STUDIO_LLM_MONTHLY_CAP_USD"))
    ledger_path = Path(repository_root) / "data" / "llm_spend.sqlite"
    ledger = SpendLedger(ledger_path, monthly_cap)
    client = OpenAICompatibleClient(settings, api_key, ledger)

    workspace = ProposalWorkspace(repository_root)
    research_tools = build_research_tool_registry()
    workspace_tools = build_workspace_tool_registry(workspace)
    registry = ToolRegistry(
        list(research_tools._tools.values()) + list(workspace_tools._tools.values())
    )
    runtime = AgentToolRuntime(client, registry, live_approved=True)
    orchestrator = MultiAgentOrchestrator(
        runtime, checkpoint_loader=checkpoint_loader, checkpoint_saver=checkpoint_saver,
    )
    return LiveStudio(orchestrator=orchestrator, workspace=workspace)