import unittest

from agent.growth_launch import LaunchBriefError, build_launch_assets, execute_growth_task


class GrowthLaunchTests(unittest.TestCase):
    def setUp(self):
        self.brief = {
            "product_name": "Example Utility",
            "target_user": "independent professionals",
            "user_problem": "they need to clarify small changes to client work",
            "desired_outcome": "a reviewable change summary",
            "features": ["structured inputs", "editable summary"],
            "limitations": ["No client messaging"],
        }

    def test_creates_private_positioning_listing_and_approval_checklist(self):
        result = build_launch_assets(self.brief)
        self.assertIn("positioning_statement", result["positioning"])
        self.assertEqual(result["listing_draft"]["publication_status"], "private_draft_only")
        self.assertFalse(result["external_actions_performed"])
        self.assertEqual(result["listing_draft"]["unverified_claims"], [])
        self.assertTrue(any(x["status"] == "mandatory_gate" for x in result["launch_checklist"]))

    def test_evidence_claim_requires_supplied_https_source(self):
        brief = dict(self.brief, verified_facts=[{"claim": "Used by 100 customers", "source_url": "http://example.com"}])
        with self.assertRaisesRegex(LaunchBriefError, "HTTPS"):
            build_launch_assets(brief)

    def test_missing_product_brief_fails_closed(self):
        with self.assertRaisesRegex(LaunchBriefError, "product_name"):
            build_launch_assets({"target_user": "someone"})

    def test_task_executor_does_not_publish_or_contact_users(self):
        result = execute_growth_task({"launch_brief": self.brief})
        self.assertTrue(result["ok"])
        self.assertFalse(result["artifact"]["external_actions_performed"])
        self.assertEqual(result["artifact"]["listing_draft"]["publication_status"], "private_draft_only")


if __name__ == "__main__":
    unittest.main()
