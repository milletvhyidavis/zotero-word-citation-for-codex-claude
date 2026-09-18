#!/usr/bin/env python3
"""Install the zotero-word-live-citations skill for Claude Code and/or Codex.

Stdlib only. Copies skills/zotero-word-live-citations/ (without tests and
caches) into the skills directory of the chosen agent:

  claude  -> ~/.claude/skills/zotero-word-live-citations   (or <project>/.claude/skills/...)
  codex   -> $CODEX_HOME/skills/zotero-word-live-citations (default ~/.codex/skills/...)

Examples:
  python install.py --target claude
  python install.py --target both --dry-run
  python install.py --target claude --project D:/papers/my-review
  python install.py --target codex --uninstall
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path

SKILL_NAME = "zotero-word-live-citations"
SOURCE = Path(__file__).resolve().parent / "skills" / SKILL_NAME
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "tests")


def target_dirs(target: str, project: str | None) -> list[tuple[str, Path]]:
    dirs: list[tuple[str, Path]] = []
    if target in ("claude", "both"):
        base = Path(project).expanduser().resolve() / ".claude" if project else Path.home() / ".claude"
        dirs.append(("claude", base / "skills" / SKILL_NAME))
    if target in ("codex", "both"):
        if project:
            base = Path(project).expanduser().resolve() / ".codex"
        else:
            base = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        dirs.append(("codex", base / "skills" / SKILL_NAME))
    return dirs


def source_files(root: Path) -> set[str]:
    files = set()
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if path.is_file() and not any(p in ("__pycache__", "tests", ".pytest_cache") for p in rel.parts) \
                and path.suffix != ".pyc":
            files.add(rel.as_posix())
    return files


def diff(src: Path, dst: Path) -> dict[str, list[str]]:
    a, b = source_files(src), source_files(dst)
    changed = sorted(f for f in a & b if not filecmp.cmp(src / f, dst / f, shallow=False))
    return {"added": sorted(a - b), "changed": changed, "removed": sorted(b - a)}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", choices=["claude", "codex", "both"], required=True)
    parser.add_argument("--project", help="install into <project>/.claude/skills (or .codex/skills) instead of the home dir")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    parser.add_argument("--force", action="store_true", help="replace an existing, different installation")
    parser.add_argument("--uninstall", action="store_true", help="remove the installed skill directory")
    args = parser.parse_args(argv)

    if not (SOURCE / "SKILL.md").is_file():
        print(f"error: skill source not found at {SOURCE}", file=sys.stderr)
        return 2
    status = 0
    for agent, dest in target_dirs(args.target, args.project):
        prefix = "[dry-run] " if args.dry_run else ""
        if args.uninstall:
            if not dest.exists():
                print(f"{agent}: not installed ({dest})")
                continue
            if not (dest / "SKILL.md").is_file():
                print(f"{agent}: refusing to remove {dest}: no SKILL.md (not a skill directory)", file=sys.stderr)
                status = 1
                continue
            print(f"{prefix}{agent}: remove {dest}")
            if not args.dry_run:
                shutil.rmtree(dest)
            continue

        if dest.exists():
            changes = diff(SOURCE, dest)
            if not any(changes.values()):
                print(f"{agent}: already up to date ({dest})")
                continue
            print(f"{agent}: existing installation differs ({dest})")
            for kind, files in changes.items():
                for name in files:
                    print(f"  {kind:8} {name}")
            if not args.force:
                print(f"{agent}: re-run with --force to replace it", file=sys.stderr)
                status = 1
                continue
            print(f"{prefix}{agent}: replace {dest}")
            if not args.dry_run:
                shutil.rmtree(dest)
                shutil.copytree(SOURCE, dest, ignore=IGNORE)
        else:
            print(f"{prefix}{agent}: install -> {dest}")
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(SOURCE, dest, ignore=IGNORE)
    if status == 0 and not args.dry_run and not args.uninstall:
        print("done. Start a new Claude Code / Codex session so the skill is discovered;"
              " then run scripts/selftest.py from the installed directory to check the environment.")
    return status


if __name__ == "__main__":
    sys.exit(main())
