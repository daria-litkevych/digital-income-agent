"""Safe, read-only public source retrieval with DNS-pinned HTTPS requests."""
from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urlparse

from agent.tool_runtime import AgentTool, ToolRegistry
from agent.evidence_store import EvidenceStore


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
            self.parts.append("\\n")

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if not self._skip_depth:
            clean = " ".join(data.split())
            if clean:
                self.parts.append(clean)


def _default_resolver(host: str) -> list[str]:
    return sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})


def _resolve_public_addresses(host: str, resolver: Callable[[str], list[str]]) -> list[str]:
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        addresses = [host]
    else:
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
    return addresses


def validate_public_https_url(url: str, resolver: Callable[[str], list[str]] = _default_resolver) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SourceFetchError("Only absolute HTTPS URLs are allowed.")
    try:
        port = parsed.port
    except ValueError as error:
        raise SourceFetchError("Invalid URL port.") from error
    if parsed.username or parsed.password or port not in (None, 443):
        raise SourceFetchError("Credentials and non-standard ports are not allowed.")
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise SourceFetchError("Local hostnames are not allowed.")
    _resolve_public_addresses(host, resolver)
    return url


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection pinned to an already validated public IP address."""
    def __init__(self, host: str, address: str, timeout: int):
        super().__init__(host=host, port=443, timeout=timeout, context=ssl.create_default_context())
        self._pinned_address = address

    def connect(self):
        raw_socket = socket.create_connection((self._pinned_address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


def _network_transport(url: str, timeout: int, max_bytes: int) -> dict[str, Any]:
    parsed = urlparse(url)
    if not parsed.hostname:
        raise SourceFetchError("Source URL has no hostname.")
    addresses = _resolve_public_addresses(parsed.hostname.lower().rstrip("."), _default_resolver)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    last_error: Exception | None = None
    for address in addresses:
        connection = _PinnedHTTPSConnection(parsed.hostname, address, timeout)
        try:
            connection.request("GET", path, headers={
                "Host": parsed.netloc,
                "User-Agent": "DigitalProductStudioResearch/1.0",
                "Accept": "text/html,text/plain,application/xhtml+xml,application/xml,text/xml,application/rss+xml",
                "Connection": "close",
            })
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise SourceFetchError("HTTP redirects are not followed.")
            if response.status < 200 or response.status >= 300:
                raise SourceFetchError(f"Public source returned HTTP {response.status}.")
            content_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SourceFetchError("Source exceeds the configured response-size limit.")
            return {"final_url": url, "content_type": content_type, "body": body}
        except SourceFetchError:
            raise
        except (OSError, TimeoutError, http.client.HTTPException) as error:
            last_error = error
        finally:
            connection.close()
    raise SourceFetchError(f"Public source fetch failed: {last_error}")


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
    evidence_store: EvidenceStore | None = None,
) -> ToolRegistry:
    """Create an explicit registry; no network tool is enabled unless this is called."""
    tools = [AgentTool(
        name="fetch_public_url",
        description="Fetch and extract a bounded amount of text from a public HTTPS source.",
        handler=lambda args: fetch_public_source(args["url"], transport=transport, resolver=resolver),
        required_arguments=("url",),
        allowed_arguments=("url",),
        allowed_roles=("market_researcher", "business_analyst", "product_strategist", "quality_controller"),
    )]
    if evidence_store is not None:
        def fetch_and_record(args: dict[str, Any]) -> dict[str, Any]:
            record = next(
                (row for row in evidence_store._load()["records"] if row.get("evidence_id") == args["evidence_id"]),
                None,
            )
            if record is None:
                raise SourceFetchError("Evidence record was not found.")
            if record.get("source_url") != args["url"]:
                raise SourceFetchError("Requested URL does not match the evidence record.")
            fetched = fetch_public_source(args["url"], transport=transport, resolver=resolver)
            try:
                stored = evidence_store.enrich_source(args["evidence_id"], fetched)
            except ValueError as error:
                raise SourceFetchError(str(error)) from error
            return {"source": fetched, "stored": stored}

        tools.append(AgentTool(
            name="fetch_and_record_evidence",
            description="Fetch the exact public HTTPS URL attached to an existing evidence ID, then store a bounded, hash-addressed excerpt as ungraded untrusted source material.",
            handler=fetch_and_record,
            required_arguments=("evidence_id", "url"),
            allowed_arguments=("evidence_id", "url"),
            allowed_roles=("market_researcher", "business_analyst", "product_strategist", "quality_controller"),
        ))
    return ToolRegistry(tools)