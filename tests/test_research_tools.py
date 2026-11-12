import unittest

from agent.engine import execute
from unittest.mock import patch

from agent.research_tools import _PinnedHTTPSConnection
from agent.research_tools import (
    SourceFetchError, build_research_tool_registry, fetch_public_source,
    validate_public_https_url,
)


PUBLIC_RESOLVER = lambda host: ["93.184.216.34"]


class ResearchToolAcceptanceTests(unittest.TestCase):
    def test_ab008_acceptance_handler_checks_source_tool_and_tests(self):
        result = execute(
            {"id": "AB-008", "role": "market_researcher", "kind": "research_tools"},
            {}, {},
        )
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))


class PublicSourceSafetyTests(unittest.TestCase):
    def test_only_public_https_urls_are_allowed(self):
        self.assertEqual(
            validate_public_https_url("https://example.test/page", PUBLIC_RESOLVER),
            "https://example.test/page",
        )
        for url in (
            "http://example.test/page",
            "https://localhost/page",
            "https://127.0.0.1/page",
            "https://example.test:8443/page",
            "https://user:pass@example.test/page",
        ):
            with self.subTest(url=url):
                with self.assertRaises(SourceFetchError):
                    validate_public_https_url(url, PUBLIC_RESOLVER)

    def test_https_connection_uses_validated_ip_not_a_second_dns_lookup(self):
        class FakeSocket:
            pass
        class FakeContext:
            def wrap_socket(self, raw_socket, server_hostname):
                self.server_hostname = server_hostname
                return raw_socket
        fake_socket = FakeSocket()
        context = FakeContext()
        with patch('agent.research_tools.ssl.create_default_context', return_value=context), patch('agent.research_tools.socket.create_connection', return_value=fake_socket) as connect:
            connection = _PinnedHTTPSConnection('example.test', '93.184.216.34', 5)
            connection.connect()
            self.assertEqual(connection.sock, fake_socket)
            connect.assert_called_once_with(('93.184.216.34', 443), 5)
            self.assertEqual(context.server_hostname, 'example.test')
            connection.close()
    def test_private_dns_resolution_is_rejected(self):
        with self.assertRaisesRegex(SourceFetchError, "Private"):
            validate_public_https_url(
                "https://public-looking.example",
                lambda host: ["10.0.0.5"],
            )

    def test_html_text_is_extracted_without_script_content(self):
        def transport(url, timeout, max_bytes):
            return {
                "final_url": url,
                "content_type": "text/html",
                "body": b"<html><head><title>Useful page</title></head><body><h1>Hello</h1><script>secret()</script><p>Public facts</p></body></html>",
            }
        result = fetch_public_source(
            "https://example.test/page", transport=transport,
            resolver=PUBLIC_RESOLVER,
        )
        self.assertEqual(result["title"], "Useful page")
        self.assertIn("Hello", result["text"])
        self.assertIn("Public facts", result["text"])
        self.assertNotIn("secret", result["text"])
        self.assertEqual(result["source_class"], "ungraded_public_source")

    def test_redirect_to_private_address_is_rejected(self):
        def transport(url, timeout, max_bytes):
            return {
                "final_url": "https://127.0.0.1/private",
                "content_type": "text/plain",
                "body": b"not safe",
            }
        with self.assertRaises(SourceFetchError):
            fetch_public_source(
                "https://example.test/page", transport=transport,
                resolver=lambda host: ["93.184.216.34"] if host == "example.test" else ["127.0.0.1"],
            )

    def test_binary_content_and_oversized_content_are_rejected(self):
        def binary(url, timeout, max_bytes):
            return {"final_url": url, "content_type": "application/pdf", "body": b"%PDF"}
        with self.assertRaisesRegex(SourceFetchError, "Unsupported"):
            fetch_public_source("https://example.test/a", transport=binary, resolver=PUBLIC_RESOLVER)

        def oversized(url, timeout, max_bytes):
            return {"final_url": url, "content_type": "text/plain", "body": b"x" * (max_bytes + 1)}
        with self.assertRaisesRegex(SourceFetchError, "size limit"):
            fetch_public_source(
                "https://example.test/a", transport=oversized,
                resolver=PUBLIC_RESOLVER, max_bytes=10,
            )

    def test_registry_exposes_only_the_explicit_read_only_fetch_tool(self):
        registry = build_research_tool_registry(
            transport=lambda url, timeout, max_bytes: {
                "final_url": url, "content_type": "text/plain", "body": b"Evidence text"
            },
            resolver=PUBLIC_RESOLVER,
        )
        self.assertEqual([x["name"] for x in registry.descriptions()], ["fetch_public_url"])
        result = registry.invoke("fetch_public_url", {"url": "https://example.test/source"}, role="market_researcher")
        self.assertEqual(result["text"], "Evidence text")


if __name__ == "__main__":
    unittest.main()
