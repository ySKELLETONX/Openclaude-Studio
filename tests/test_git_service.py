from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from openclaude_studio.services.git_service import GitService


@unittest.skipUnless(shutil.which("git"), "Git is required for this test")
class GitServiceTests(unittest.TestCase):
    def test_status_detects_repo_and_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            (root / "demo.txt").write_text("hello", encoding="utf-8")
            service = GitService()
            status = service.status(str(root))
            self.assertTrue(status.available)
            self.assertTrue(status.repo_found)
            self.assertTrue(any(item.path == "demo.txt" for item in status.files))


if __name__ == "__main__":
    unittest.main()
