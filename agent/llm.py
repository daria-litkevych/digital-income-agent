"""Provider-neutral LLM interface with offline default and explicit live client."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request as HTTPRequest, urlopen
from uuid import uuid4

from agent.spend_ledger import SpendLedger


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
    """Explicit configuration contract; live mode is never enabled implicitly."""
    enabled: bool = False
    provider: str = ""
    base_url: str = ""
    model: str = ""
    max_output_tokens: int = 512
    max_input_characters: int = 12000
    max_cost_per_call_usd: float = 0.0
    input_price_per_million_usd: float | None = None
    output_price_per_million_usd: float | None = None
    timeout_seconds: int = 30

    def validate_for_live_use(self) -> None:
        if not self.enabled:
            raise RuntimeError("Live LLM is disabled. Offline mode is the default.")
        if not all(x.strip() for x in (self.provider, self.base_url, self.model)):
            raise ValueError("provider, base_url and model are required")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Live provider endpoint must use HTTPS")
        if self.max_cost_per_call_usd <= 0:
            raise ValueError("A positive per-call spending cap is required")
        if self.input_price_per_million_usd is None or self.output_price_per_million_usd is None:
            raise ValueError("Verified input and output prices are required")
        if min(self.input_price_per_million_usd, self.output_price_per_million_usd) < 0:
            raise ValueError("Token prices cannot be negative")
        if self.max_output_tokens < 1 or self.max_input_characters < 1 or self.timeout_seconds < 1:
            raise ValueError("Input, output and timeout limits must be positive")


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
    """Fail closed before a provider call."""
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


class OpenAICompatibleClient:
    """Minimal text-chat client. Constructing it does not send a request.

    The caller must explicitly provide the API key and enabled settings. Never
    put credentials in repository files or log request headers.
    """
    def __init__(self, settings: LLMSettings, api_key: str,
                 spend_ledger: SpendLedger):
        settings.validate_for_live_use()
        if not api_key or not api_key.strip():
            raise ValueError("An API key must be explicitly supplied at runtime")
        self.settings = settings
        if not isinstance(spend_ledger, SpendLedger):
            raise TypeError("A persistent SpendLedger is required for live use")
        self._api_key = api_key
        self.spend_ledger = spend_ledger

    def generate(self, request: LLMRequest,
                 request_id: str | None = None) -> LLMResponse:
        enforce_request_limits(request, self.settings)
        reservation_id = request_id or str(uuid4())
        prompt_size = len(request.system) + len(request.user)
        estimated_input_tokens = (prompt_size + 3) // 4
        reserved_cost = estimate_cost_usd(
            estimated_input_tokens, request.max_output_tokens,
            self.settings.input_price_per_million_usd or 0.0,
            self.settings.output_price_per_million_usd or 0.0,
        )
        if self.spend_ledger is not None:
            self.spend_ledger.reserve(reservation_id, reserved_cost)
        endpoint = self.settings.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "max_tokens": request.max_output_tokens,
            "temperature": 0.2,
        }
        http_request = HTTPRequest(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=self.settings.timeout_seconds) as response:
                raw = response.read()
        except URLError as error:
            raise RuntimeError(f"LLM provider request failed: {error.reason}") from error

        try:
            body = json.loads(raw.decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            usage = body["usage"]
            input_tokens = int(usage["prompt_tokens"])
            output_tokens = int(usage["completion_tokens"])
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as error:
            raise RuntimeError("LLM provider returned an unexpected response format") from error
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("LLM provider returned an empty or non-text response")
        cost = estimate_cost_usd(
            input_tokens, output_tokens,
            self.settings.input_price_per_million_usd or 0.0,
            self.settings.output_price_per_million_usd or 0.0,
        )
        if self.spend_ledger is not None:
            self.spend_ledger.settle(reservation_id, cost)
        return LLMResponse(
            text=text, model=self.settings.model, provider=self.settings.provider,
            input_tokens=input_tokens, output_tokens=output_tokens,
            estimated_cost_usd=cost, is_mock=False,
        )
