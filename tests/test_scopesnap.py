import unittest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "products" / "scopesnap" / "app" / "index.html"

class ScopeSnapPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = APP.read_text(encoding="utf-8")

    def test_core_inputs_and_actions_exist(self):
        for element_id in ["scope", "change", "hours", "rate", "costs", "currency", "timeline", "preview", "total", "copy", "print"]:
            self.assertIn(f'id="{element_id}"', self.html)

    def test_first_mvp_does_not_use_external_services_or_persist_data(self):
        self.assertNotRegex(self.html, r'<script[^>]+src=')
        self.assertNotRegex(self.html, r'<link[^>]+href=["\']https?://')
        for forbidden in ["localStorage", "sessionStorage", "XMLHttpRequest", "fetch("]:
            self.assertNotIn(forbidden, self.html)

    def test_disclaimer_and_privacy_notice_are_present(self):
        self.assertIn("not a contract or legal advice", self.html)
        self.assertIn("does not send your entries to a server", self.html)

    def test_calculation_and_print_workflows_are_present(self):
        self.assertIn("num(\"hours\")*num(\"rate\")", self.html)
        self.assertIn("window.print()", self.html)
        self.assertIn("navigator.clipboard.writeText", self.html)

if __name__ == "__main__":
    unittest.main()
