"""Safe, read-only public source retrieval tools for specialist agents."""
from __future__ import annotations

import ipaddress
import socket
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from agent.tool_runtime import AgentTool, ToolRegistry


class SourceFetchError(RuntimeError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "li", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if not self._skip_depth:
            clean = " ".join(data.split())
            if clean:
                self.parts.append(clean)


def _default_resolver(host: str) -> list[str]:
    return sorted({item[4][0] for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)})


def validate_public_https_url(url: str, resolver: Callable[[str], list[str]] = _default_resolver) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SourceFetchError("Only absolute HTTPS URLs are allowed.")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise SourceFetchError("Credentials and non-standard ports are not allowed.")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise SourceFetchError("Local hostnames are not allowed.")
    try:
        addresses = resolver(host)
    except (OSError, ValueError) as error:
        raise SourceFetchError("Could not safely resolve source hostname.") from error
    if not addresses:
        raise SourceFetchError("Source hostname did not resolve.")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as error:
            raise SourceFetchError("Resolver returned an invalid IP address.") from error
        if not ip.is_global:
            raise SourceFetchError("Private, local or reserved network addresses are not allowed.")
    return url


def _network_transport(url: str, timeout: int, max_bytes: int) -> dict[str, Any]:
    request = Request(url, headers={
        "User-Agent": "DigitalProductStudioResearch/1.0",
        "Accept": "text/html,text/plain,application/xhtml+xml,application/xml,text/xml,application/rss+xml",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            body = response.read(max_bytes + 1)
            final_url = response.geturl()
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise SourceFetchError(f"Public source fetch failed: {error}") from error
    if len(body) > max_bytes:
        raise SourceFetchError("Source exceeds the configured response-size limit.")
    return {"final_url": final_url, "content_type": content_type, "body": body}


def fetch_public_source(
    url: str,
    *,
    transport: Callable[[str, int, int], dict[str, Any]] = _network_transport,
    resolver: Callable[[str], list[str]] = _default_resolver,
    timeout: int = 12,
    max_bytes: int = 200_000,
    max_text_characters: int = 12_000,
) -> dict[str, Any]:
    validate_public_https_url(url, resolver)
    response = transport(url, timeout, max_bytes)
    final_url = response.get("final_url", url)
    validate_public_https_url(final_url, resolver)
    content_type = str(response.get("content_type", "")).lower()
    if content_type not in {
        "text/html", "application/xhtml+xml", "text/plain",
        "application/xml", "text/xml", "application/rss+xml",
    }:
        raise SourceFetchError("Unsupported or non-text source content type.")
    body = response.get("body", b"")
    if not isinstance(body, bytes) or len(body) > max_bytes:
        raise SourceFetchError("Source response is invalid or exceeds size limit.")
    decoded = body.decode("utf-8", errors="replace")
    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = _TextExtractor()
        parser.feed(decoded)
        title = " ".join(" ".join(parser.title_parts).split())[:300]
        text = " ".join(" ".join(parser.parts).split())
    else:
        title = ""
        text = " ".join(decoded.split())
    return {
        "url": final_url,
        "requested_url": url,
        "title": title,
        "content_type": content_type,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "text": text[:max_text_characters],
        "truncated": len(text) > max_text_characters,
        "source_class": "ungraded_public_source",
        "evidence_note": "Retrieval is not verification. Grade source authority and claim support separately.",
    }


def build_research_tool_registry(
    *,
    transport: Callable[[str, int, int], dict[str, Any]] = _network_transport,
    resolver: Callable[[str], list[str]] = _default_resolver,
) -> ToolRegistry:
    """Create an explicit registry; no network tool is enabled unless this is called."""
    return ToolRegistry([AgentTool(
        name="fetch_public_url",
        description="Fetch and extract a bounded amount of text from a public HTTPS source.",
        handler=lambda args: fetch_public_source(
            args["url"], transport=transport, resolver=resolver,
        ),
        required_arguments=("url",),
        allowed_arguments=("url",),
    )])
