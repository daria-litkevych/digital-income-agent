"""Guarded role-dispatch layer for the Digital Product Studio.

The brain separates role instructions, model invocation, output validation and
permission checks. It is intentionally not activated by the scheduled workflow:
offline mode is the default and live provider use requires explicit approval.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from agent.llm import LLMClient, LLMRequest, OfflineMockClient


@dataclass(frozen=True)
class RoleSpec:
    name: str
    mission: str
    allowed_outputs: tuple[str, ...]
    forbidden_actions: tuple[str, ...] = (
        "spend money", "publish content", "contact people",
        "change account settings", "access private accounts",
    )


ROLE_REGISTRY: dict[str, RoleSpec] = {
    "project_manager": RoleSpec(
        "Project Manager",
        "Prioritise tasks, enforce dependencies, preserve continuity and surface material decisions.",
        ("task_plan", "status_summary", "decision_request"),
    ),
    "market_researcher": RoleSpec(
        "Market Researcher",
        "Organise source-linked public evidence about users, alternatives, competitors and pricing.",
        ("evidence_records", "research_summary", "open_questions"),
    ),
    "business_analyst": RoleSpec(
        "Business Analyst",
        "Compare evidence, business models, build effort, distribution and commercial risks.",
        ("comparison", "assumptions", "risk_register"),
    ),
    "product_strategist": RoleSpec(
        "Product Strategist",
        "Translate a supported user problem into a narrow product hypothesis and validation plan.",
        ("product_hypothesis", "validation_plan", "decision_memo"),
    ),
    "product_designer": RoleSpec(
        "Product Designer",
        "Define user journeys, information architecture, interface requirements and acceptance criteria.",
        ("user_journey", "wireframe_spec", "acceptance_criteria"),
    ),
    "developer": RoleSpec(
        "Developer",
        "Produce implementation plans and code changes constrained by approved product requirements.",
        ("implementation_plan", "code_patch", "test_plan"),
    ),
    "quality_controller": RoleSpec(
        "Quality Controller",
        "Check claims, sources, output contracts, product behaviour and release-blocking risks.",
        ("audit_report", "test_results", "release_recommendation"),
    ),
    "growth_launch": RoleSpec(
        "Growth & Launch",
        "Prepare positioning, listing materials, pricing hypotheses and private launch checklists.",
        ("positioning", "listing_draft", "launch_checklist"),
    ),
    "analytics": RoleSpec(
        "Analytics Specialist",
        "Analyse supplied product metrics and recommend evidence-based iteration or retirement.",
        ("metrics_report", "experiment_recommendation", "decision_memo"),
    ),
}

FORBIDDEN_REQUESTS = (
    "send email", "send message", "contact customer", "contact prospect",
    "publish", "deploy", "purchase", "buy subscription", "top up",
    "change billing", "change permissions", "delete account",
)


class BrainError(RuntimeError):
    """Raised when a role output cannot safely be used."""


class AgentBrain:
    """Role-aware structured dispatcher over an injected LLM client."""

    def __init__(self, client: LLMClient, *, live_approved: bool = False):
        self.client = client
        self.live_approved = live_approved

    @property
    def mode(self) -> str:
        return "live" if self.live_approved and not isinstance(self.client, OfflineMockClient) else "offline"

    def dispatch(self, role: str, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if role not in ROLE_REGISTRY:
            raise BrainError(f"Unknown specialist role: {role}")
        if not task.strip():
            raise ValueError("Task description is required")
        # Never invoke a live-capable client unless live mode was explicitly approved.
        if not self.live_approved and not isinstance(self.client, OfflineMockClient):
            raise BrainError("Live model client is not approved; refusing provider invocation.")
        task_lower = task.lower()
        if any(term in task_lower for term in FORBIDDEN_REQUESTS):
            raise BrainError("This task requests an external side effect; explicit approval is required outside the agent.")

        spec = ROLE_REGISTRY[role]
        system = (
            f"You are {spec.name}, a specialist in a private digital-product studio.\n"
            f"Mission: {spec.mission}\n"
            "Use only the supplied context. Do not invent sources, facts, prices, customer quotes or test results. "
            "Separate evidence from assumptions and mark missing evidence explicitly. "
            "Do not reveal hidden reasoning; return concise conclusions and auditable evidence. "
            "Never perform or claim to perform external actions.\n"
            f"Allowed output sections: {', '.join(spec.allowed_outputs)}.\n"
            "Return exactly one JSON object with keys: status, summary, artifact, evidence, assumptions, risks, "
            "confidence, requires_human_approval. status must be one of: draft, needs_evidence, blocked. "
            "requires_human_approval must be true for any material decision or external side effect."
        )
        user = json.dumps({
            "task": task,
            "context": context,
            "role": role,
            "forbidden_actions": list(spec.forbidden_actions),
        }, ensure_ascii=False, sort_keys=True)
        response = self.client.generate(LLMRequest(
            task=f"{role}:{task[:100]}",
            system=system,
            user=user,
            max_output_tokens=900,
        ))
        if response.is_mock:
            return {
                "status": "draft",
                "summary": "Offline mock only; no specialist reasoning or research was performed.",
                "artifact": {},
                "evidence": [],
                "assumptions": [],
                "risks": ["Mock output is not a usable work product or evidence."],
                "confidence": "none",
                "requires_human_approval": True,
                "execution_mode": "offline_mock",
                "raw_response": response.text,
            }
        try:
            payload = json.loads(response.text)
        except (TypeError, json.JSONDecodeError) as error:
            raise BrainError("Specialist response was not valid JSON.") from error
        required = {
            "status", "summary", "artifact", "evidence", "assumptions",
            "risks", "confidence", "requires_human_approval",
        }
        if not isinstance(payload, dict) or not required.issubset(payload):
            raise BrainError("Specialist response is missing required contract fields.")
        if payload["status"] not in {"draft", "needs_evidence", "blocked"}:
            raise BrainError("Specialist response contains an unsupported status.")
        if not isinstance(payload["summary"], str) or not payload["summary"].strip():
            raise BrainError("Specialist response has no summary.")
        if not isinstance(payload["requires_human_approval"], bool):
            raise BrainError("Human-approval flag must be boolean.")
        if not all(isinstance(payload[key], list) for key in ("evidence", "assumptions", "risks")):
            raise BrainError("Evidence, assumptions and risks must be arrays.")
        payload["execution_mode"] = "live"
        payload["model"] = response.model
        payload["provider"] = response.provider
        payload["estimated_cost_usd"] = response.estimated_cost_usd
        payload["is_mock"] = False
        return payload


def build_offline_brain() -> AgentBrain:
    """Safe default factory. Never enables or configures a paid provider."""
    return AgentBrain(OfflineMockClient(), live_approved=False)
