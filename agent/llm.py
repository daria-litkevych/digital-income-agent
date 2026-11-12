"""Provider-neutral LLM interface with a safe, offline default."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class LLMRequest:
    task: str
    system: str
    user: str
    max_output_tokens: int = 512

@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float = 0.0
    is_mock: bool = True

class LLMClient(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse: ...

class OfflineMockClient:
    """Deterministic test client; never makes a network request."""
    def generate(self, request: LLMRequest) -> LLMResponse:
        if not request.task.strip() or not request.user.strip():
            raise ValueError("task and user prompt must not be empty")
        if request.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be positive")
        return LLMResponse(
            text="[MOCK RESPONSE — no model was called]\n"
                 f"Task: {request.task}\n"
                 "Placeholder only; this is not research evidence.",
            model="offline-mock", provider="local-test",
            input_tokens=0, output_tokens=0, estimated_cost_usd=0.0, is_mock=True,
        )

@dataclass(frozen=True)
class LLMSettings:
    """Explicit configuration contract; no live API is implemented or enabled."""
    enabled: bool = False
    provider: str = ""
    base_url: str = ""
    model: str = ""
    max_output_tokens: int = 512
    max_input_characters: int = 12000
    max_cost_per_call_usd: float = 0.0
    input_price_per_million_usd: float | None = None
    output_price_per_million_usd: float | None = None

    def validate_for_live_use(self) -> None:
        if not self.enabled:
            raise RuntimeError("Live LLM is disabled. Offline mode is the default.")
        if not all(x.strip() for x in (self.provider, self.base_url, self.model)):
            raise ValueError("provider, base_url and model are required")
        if self.max_cost_per_call_usd <= 0:
            raise ValueError("A positive per-call spending cap is required")
        if self.input_price_per_million_usd is None or self.output_price_per_million_usd is None:
            raise ValueError("Verified input and output prices are required")
        if min(self.input_price_per_million_usd, self.output_price_per_million_usd) < 0:
            raise ValueError("Token prices cannot be negative")
        if self.max_output_tokens < 1 or self.max_input_characters < 1:
            raise ValueError("Input and output limits must be positive")

def estimate_cost_usd(input_tokens: int, output_tokens: int,
                      input_price_per_million_usd: float,
                      output_price_per_million_usd: float) -> float:
    if min(input_tokens, output_tokens) < 0:
        raise ValueError("Token counts cannot be negative")
    if min(input_price_per_million_usd, output_price_per_million_usd) < 0:
        raise ValueError("Token prices cannot be negative")
    return (input_tokens * input_price_per_million_usd
            + output_tokens * output_price_per_million_usd) / 1_000_000

def enforce_request_limits(request: LLMRequest, settings: LLMSettings) -> None:
    """Fail closed before a future provider call."""
    settings.validate_for_live_use()
    prompt_size = len(request.system) + len(request.user)
    if prompt_size > settings.max_input_characters:
        raise ValueError(f"Prompt has {prompt_size} characters; limit is {settings.max_input_characters}")
    if request.max_output_tokens > settings.max_output_tokens:
        raise ValueError("Requested output limit exceeds configured limit")
    # Planning estimate only: provider tokenization and billing may differ.
    estimated_input_tokens = (prompt_size + 3) // 4
    estimate = estimate_cost_usd(
        estimated_input_tokens, request.max_output_tokens,
        settings.input_price_per_million_usd or 0.0,
        settings.output_price_per_million_usd or 0.0,
    )
    if estimate > settings.max_cost_per_call_usd:
        raise ValueError("Estimated request cost exceeds per-call cap")
