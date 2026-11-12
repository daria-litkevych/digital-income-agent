import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"

class DashboardOpportunityTests(unittest.TestCase):
    def test_dashboard_displays_cross_market_opportunities(self):
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("opportunity_scan", html)
        self.assertIn("B2C / B2B / Prosumer", html)
        self.assertIn("Первый MVP-кандидат", html)

    def test_dashboard_keeps_original_horeca_competitor_section(self):
        html = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("cafe_starter_kit", html)
        self.assertIn("shiftbrief_ai", html)

if __name__ == "__main__":
    unittest.main()
