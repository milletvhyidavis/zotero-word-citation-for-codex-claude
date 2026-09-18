"""install.py: dry-run, install, idempotence, --force on changes, uninstall."""

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("install", REPO / "install.py")
install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = install.main(list(argv))
    return code, out.getvalue() + err.getvalue()


class InstallTests(unittest.TestCase):
    def test_project_install_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / ".claude" / "skills" / install.SKILL_NAME
            code, _ = run("--target", "claude", "--project", tmp, "--dry-run")
            self.assertEqual(code, 0)
            self.assertFalse(dest.exists())

            self.assertEqual(run("--target", "claude", "--project", tmp)[0], 0)
            self.assertTrue((dest / "SKILL.md").is_file())
            self.assertTrue((dest / "scripts" / "insert_zotero_fields.py").is_file())
            self.assertFalse((dest / "tests").exists())
            self.assertIn("already up to date", run("--target", "claude", "--project", tmp)[1])

            (dest / "SKILL.md").write_text("local edit", encoding="utf-8")
            code, text = run("--target", "claude", "--project", tmp)
            self.assertEqual(code, 1)
            self.assertIn("changed  SKILL.md", text)
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "local edit")
            self.assertEqual(run("--target", "claude", "--project", tmp, "--force")[0], 0)
            self.assertNotEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "local edit")

            self.assertEqual(run("--target", "claude", "--project", tmp, "--uninstall")[0], 0)
            self.assertFalse(dest.exists())

    def test_codex_home_respected(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"CODEX_HOME": tmp}):
            dirs = install.target_dirs("both", None)
        self.assertEqual(dirs[1], ("codex", Path(tmp) / "skills" / install.SKILL_NAME))
        self.assertEqual(dirs[0][0], "claude")


if __name__ == "__main__":
    unittest.main()
