import unittest

from agent.product_designer import DesignBriefError, build_design_artifact, execute_design_task


class ProductDesignerTests(unittest.TestCase):
    def setUp(self):
        self.brief = {
            "target_user": "A generic independent professional",
            "user_problem": "They lose track of requested changes.",
            "desired_outcome": "A clear reviewable change summary",
            "constraints": ["No external integrations", "No paid services"],
        }

    def test_builds_all_role_owned_artifacts_from_supplied_brief(self):
        result = build_design_artifact(self.brief)
        self.assertEqual(set(result), {"user_journey", "wireframe_spec", "acceptance_criteria", "assumptions", "constraints", "requires_human_review"})
        self.assertEqual(result["user_journey"]["target_user"], self.brief["target_user"])
        self.assertEqual(len(result["user_journey"]["steps"]), 4)
        self.assertGreaterEqual(len(result["acceptance_criteria"]), 4)
        self.assertTrue(result["requires_human_review"])

    def test_missing_brief_fields_fail_closed(self):
        with self.assertRaisesRegex(DesignBriefError, "target_user"):
            build_design_artifact({"user_problem": "x"})

    def test_invalid_constraints_fail_closed(self):
        brief = dict(self.brief, constraints=["valid", ""])
        with self.assertRaisesRegex(DesignBriefError, "non-empty string"):
            build_design_artifact(brief)

    def test_task_executor_blocks_incomplete_brief_and_never_claims_evidence(self):
        blocked = execute_design_task({"design_brief": {"user_problem": "x"}})
        self.assertTrue(blocked["blocked"])
        result = execute_design_task({"design_brief": self.brief})
        self.assertTrue(result["ok"])
        self.assertIn("no independent customer research", result["artifact"]["assumptions"][0].lower())


if __name__ == "__main__":
    unittest.main()
