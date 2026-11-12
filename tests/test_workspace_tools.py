import tempfile
import unittest
from pathlib import Path

from agent.engine import execute
from agent.workspace_tools import ProposalWorkspace, WorkspaceError, build_workspace_tool_registry


class WorkspaceToolAcceptanceTests(unittest.TestCase):
    def test_ab009_acceptance_handler_checks_workspace_tools_and_tests(self):
        result = execute({"id": "AB-009", "role": "developer", "kind": "workspace_tools"}, {}, {})
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))


class ProposalWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        (self.repo / "agent").mkdir()
        (self.repo / "agent" / "sample.py").write_text("ORIGINAL", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_sample.py").write_text(
            "import unittest\\nclass SampleTest(unittest.TestCase):\\n def test_ok(self): self.assertEqual(1 + 1, 2)\\n",
            encoding="utf-8",
        )
        self.workspace = ProposalWorkspace(
            self.repo,
            allowed_files=("agent/sample.py", "tests/test_sample.py"),
            allowed_tests=("tests.test_sample",),
        )

    def tearDown(self):
        self.workspace.close()
        self.temp.cleanup()

    def test_proposed_edit_never_changes_repository(self):
        result = self.workspace.propose_write("agent/sample.py", "PROPOSED")
        self.assertEqual(result["status"], "proposal_only")
        self.assertFalse(result["repository_modified"])
        self.assertEqual((self.repo / "agent" / "sample.py").read_text(encoding="utf-8"), "ORIGINAL")
        self.assertEqual(self.workspace.read_file("agent/sample.py"), "PROPOSED")

    def test_path_traversal_and_unlisted_files_are_rejected(self):
        with self.assertRaises(WorkspaceError):
            self.workspace.read_file("../secrets.txt")
        with self.assertRaises(WorkspaceError):
            self.workspace.propose_write("README.md", "change")

    def test_only_allowlisted_test_module_runs(self):
        result = self.workspace.run_tests("tests.test_sample")
        self.assertTrue(result["passed"], result)
        self.assertFalse(result["repository_modified"])
        self.assertFalse(result["is_os_sandbox"])
        with self.assertRaises(WorkspaceError):
            self.workspace.run_tests("tests.test_anything")

    def test_tool_registry_exposes_only_read_propose_and_test(self):
        registry = build_workspace_tool_registry(self.workspace)
        self.assertEqual(
            [tool["name"] for tool in registry.descriptions()],
            ["read_workspace_file", "propose_workspace_edit", "run_allowlisted_tests"],
        )


if __name__ == "__main__":
    unittest.main()