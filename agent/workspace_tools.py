"""Temporary, allowlisted workspace tools for proposing and testing agent changes.

This is a constrained development workspace, not a hardened OS sandbox. It never
writes to the checked-out repository: all edits happen in a fresh temporary copy.
Only explicitly allowlisted files can be copied or changed, and only named test
modules can be invoked with a timeout.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from agent.tool_runtime import AgentTool, ToolRegistry


DEFAULT_ALLOWED_FILES = (
    "agent/brain.py",
    "agent/engine.py",
    "agent/project_manager.py",
    "agent/tool_runtime.py",
    "agent/research_tools.py",
    "tests/test_brain.py",
    "tests/test_brain_e2e.py",
    "tests/test_project_manager.py",
    "tests/test_tool_runtime.py",
    "tests/test_research_tools.py",
)
DEFAULT_ALLOWED_TESTS = (
    "tests.test_brain",
    "tests.test_brain_e2e",
    "tests.test_project_manager",
    "tests.test_tool_runtime",
    "tests.test_research_tools",
)


class WorkspaceError(RuntimeError):
    pass


class ProposalWorkspace:
    def __init__(
        self,
        repository_root: str | Path,
        *,
        allowed_files: Iterable[str] = DEFAULT_ALLOWED_FILES,
        allowed_tests: Iterable[str] = DEFAULT_ALLOWED_TESTS,
        timeout_seconds: int = 30,
    ):
        self.repository_root = Path(repository_root).resolve()
        self.allowed_files = frozenset(allowed_files)
        self.allowed_tests = frozenset(allowed_tests)
        if timeout_seconds < 1 or timeout_seconds > 60:
            raise ValueError("Workspace test timeout must be between 1 and 60 seconds.")
        self.timeout_seconds = timeout_seconds
        self._temp = tempfile.TemporaryDirectory(prefix="agent-proposal-")
        self.root = Path(self._temp.name).resolve()
        for relative in self.allowed_files:
            self._validate_relative(relative)
            source = self.repository_root / relative
            if source.is_file():
                target = self.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)

    def _validate_relative(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise WorkspaceError("Workspace paths must be non-empty POSIX relative paths.")
        path = Path(relative)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise WorkspaceError("Absolute paths and path traversal are not allowed.")
        if relative not in self.allowed_files:
            raise WorkspaceError(f"Path is not allowlisted: {relative}")
        return path

    def read_file(self, relative: str) -> str:
        path = self.root / self._validate_relative(relative)
        if not path.is_file():
            raise WorkspaceError("File is not present in the proposal workspace.")
        content = path.read_text(encoding="utf-8")
        if len(content) > 30000:
            raise WorkspaceError("File exceeds the 30,000-character read limit.")
        return content

    def propose_write(self, relative: str, content: str) -> dict:
        path = self.root / self._validate_relative(relative)
        if not isinstance(content, str) or len(content) > 30000:
            raise WorkspaceError("Proposed content must be text of at most 30,000 characters.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {
            "status": "proposal_only",
            "path": relative,
            "characters": len(content),
            "repository_modified": False,
        }

    def run_tests(self, test_module: str) -> dict:
        if test_module not in self.allowed_tests:
            raise WorkspaceError("Test module is not allowlisted.")
        module_path = test_module.replace(".", "/") + ".py"
        if module_path not in self.allowed_files or not (self.root / module_path).is_file():
            raise WorkspaceError("Allowlisted test module is unavailable in this workspace.")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-m", "unittest", test_module, "-v"],
                cwd=self.root,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise WorkspaceError("Allowlisted test command exceeded its timeout.") from error
        return {
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout[-12000:],
            "stderr": result.stderr[-12000:],
            "timeout_seconds": self.timeout_seconds,
            "repository_modified": False,
            "is_os_sandbox": False,
        }

    def close(self) -> None:
        self._temp.cleanup()


def build_workspace_tool_registry(workspace: ProposalWorkspace) -> ToolRegistry:
    return ToolRegistry([
        AgentTool(
            name="read_workspace_file",
            description="Read an allowlisted project file in the temporary proposal workspace.",
            handler=lambda args: {"path": args["path"], "content": workspace.read_file(args["path"])},
            required_arguments=("path",), allowed_arguments=("path",),
        ),
        AgentTool(
            name="propose_workspace_edit",
            description="Write a proposed change only into the temporary proposal workspace.",
            handler=lambda args: workspace.propose_write(args["path"], args["content"]),
            required_arguments=("path", "content"),
            allowed_arguments=("path", "content"),
        ),
        AgentTool(
            name="run_allowlisted_tests",
            description="Run one pre-approved unittest module in the temporary proposal workspace with a strict timeout.",
            handler=lambda args: workspace.run_tests(args["test_module"]),
            required_arguments=("test_module",), allowed_arguments=("test_module",),
        ),
    ])
