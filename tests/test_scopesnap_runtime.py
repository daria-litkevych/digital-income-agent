"""Browser-runtime smoke tests for the ScopeSnap inline JavaScript.

Requires Node.js (available on GitHub Actions Ubuntu runners). No browser or
third-party package is required: a small DOM stub executes the actual app script.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "products" / "scopesnap" / "app" / "index.html"


class ScopeSnapRuntimeTests(unittest.TestCase):
    def test_calculation_summary_and_print_action(self):
        html = APP.read_text(encoding="utf-8")
        match = re.search(r"<script>(.*?)</script>", html, re.S)
        self.assertIsNotNone(match, "Inline application script not found")
        script = match.group(1)
        harness = r'''
const vm = require("node:vm");
const source = process.argv[1];
const ids = ["business","client","project","scope","change","hours","rate","costs","currency","timeline","valid","total","preview","copy","print","toast"];
const elements = Object.fromEntries(ids.map(id => [id, {
  value: ({hours:"2",rate:"60",costs:"15",currency:"EUR"})[id] || "",
  textContent: "",
  handlers: {},
  addEventListener(type, fn) { this.handlers[type] = fn; }
}]));
let printed = false;
const context = {
  document: { getElementById: id => elements[id] },
  navigator: { clipboard: { writeText: async () => {} } },
  window: { print: () => { printed = true; } },
  Intl, Number, Math, String
};
vm.runInNewContext(source, context);
if (!elements.total.textContent.includes("135")) throw new Error("Expected €135 total, got " + elements.total.textContent);
if (!elements.preview.textContent.includes("TOTAL ADDITIONAL PRICE")) throw new Error("Missing total in generated summary");
if (!elements.preview.textContent.includes("Please confirm in writing")) throw new Error("Missing approval request");
elements.hours.value = "-3";
elements.hours.handlers.input();
if (!elements.total.textContent.includes("15")) throw new Error("Negative hours should not increase labour cost");
elements.print.handlers.click();
if (!printed) throw new Error("Print action did not call window.print()");
console.log("ScopeSnap runtime smoke test passed");
'''
        result = subprocess.run(
            ["node", "-e", harness, script],
            capture_output=True, text=True, timeout=10
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("passed", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
