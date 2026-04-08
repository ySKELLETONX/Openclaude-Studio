from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitFileStatus:
    code: str
    path: str


@dataclass
class GitRepoStatus:
    available: bool
    repo_found: bool
    root: str = ""
    branch: str = ""
    tracking: str = ""
    ahead_behind: str = ""
    files: list[GitFileStatus] = field(default_factory=list)
    summary: str = ""
    error: str = ""


class GitService:
    def status(self, workspace: str, executable: str = "git") -> GitRepoStatus:
        if not shutil.which(executable):
            return GitRepoStatus(
                available=False,
                repo_found=False,
                summary="Git executable not found.",
                error=f"Could not find '{executable}' on PATH.",
            )

        workspace_path = Path(workspace or Path.cwd())
        if not workspace_path.exists():
            return GitRepoStatus(
                available=True,
                repo_found=False,
                summary="Git workspace not found.",
                error=f"Workspace does not exist: {workspace_path}",
            )

        root_result = self._run(executable, ["rev-parse", "--show-toplevel"], workspace_path)
        if root_result.returncode != 0:
            return GitRepoStatus(
                available=True,
                repo_found=False,
                summary="No Git repository detected in this workspace.",
                error=(root_result.stderr or root_result.stdout).strip(),
            )

        repo_root = root_result.stdout.strip()
        status_result = self._run(executable, ["status", "--porcelain=1", "--branch"], Path(repo_root))
        if status_result.returncode != 0:
            return GitRepoStatus(
                available=True,
                repo_found=True,
                root=repo_root,
                summary="Git status failed.",
                error=(status_result.stderr or status_result.stdout).strip(),
            )

        lines = [line.rstrip() for line in status_result.stdout.splitlines() if line.strip()]
        branch = ""
        tracking = ""
        ahead_behind = ""
        files: list[GitFileStatus] = []
        for index, line in enumerate(lines):
            if index == 0 and line.startswith("## "):
                branch, tracking, ahead_behind = self._parse_branch_line(line[3:])
                continue
            code = line[:2].strip() or "??"
            path = line[3:].strip()
            files.append(GitFileStatus(code=code, path=path))

        summary = f"{len(files)} changed file(s)" if files else "Working tree clean."
        return GitRepoStatus(
            available=True,
            repo_found=True,
            root=repo_root,
            branch=branch,
            tracking=tracking,
            ahead_behind=ahead_behind,
            files=files,
            summary=summary,
        )

    def stage_all(self, workspace: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["add", "-A"], "All changes staged.")

    def unstage_all(self, workspace: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["reset"], "Staged changes cleared.")

    def commit(self, workspace: str, message: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["commit", "-m", message], "Commit created.")

    def pull(self, workspace: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["pull", "--ff-only"], "Pull completed.")

    def push(self, workspace: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["push"], "Push completed.")

    def fetch(self, workspace: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["fetch", "--all"], "Fetch completed.")

    def create_branch(self, workspace: str, branch_name: str, executable: str = "git") -> tuple[bool, str]:
        return self._simple(workspace, executable, ["checkout", "-b", branch_name], f"Switched to {branch_name}.")

    def _simple(self, workspace: str, executable: str, args: list[str], success_message: str) -> tuple[bool, str]:
        status = self.status(workspace, executable)
        if not status.available or not status.repo_found:
            return False, status.error or status.summary
        result = self._run(executable, args, Path(status.root))
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip() or "Git command failed."
        output = (result.stdout or result.stderr).strip()
        return True, output or success_message

    def _run(self, executable: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [executable, *args],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

    def _parse_branch_line(self, value: str) -> tuple[str, str, str]:
        branch = value
        tracking = ""
        ahead_behind = ""
        if "..." in value:
            branch, remainder = value.split("...", 1)
            tracking = remainder
        if " [" in tracking:
            tracking, status = tracking.split(" [", 1)
            ahead_behind = status.rstrip("]")
        elif " [" in branch:
            branch, status = branch.split(" [", 1)
            ahead_behind = status.rstrip("]")
        return branch.strip(), tracking.strip(), ahead_behind.strip()
