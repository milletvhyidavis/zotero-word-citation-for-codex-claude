#!/usr/bin/env python3
"""Render a DOCX with Microsoft Word (Windows, COM) to PDF and count fields.

Opens a temporary COPY read-only in a hidden Word instance, reports how many
fields Word itself parsed (total / ZOTERO_ITEM / ZOTERO_BIBL) and the page
count, exports a PDF, and closes without saving. The DOCX is never modified
and Zotero Refresh is NOT run - rendering is not proof that Refresh works.

  word_render.py document.docx --pdf document.pdf [--json]

Exit code: 0 rendered, 1 Word failed, 2 Word/PowerShell unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import EXIT_FAIL, EXIT_OK, EXIT_USAGE, dump_json, utf8_stdio  # noqa: E402

PS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$word = $null; $doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $doc = $word.Documents.Open($env:ZWLC_DOCX, $false, $true, $false)
  $total = $doc.Fields.Count; $items = 0; $bibl = 0
  foreach ($f in $doc.Fields) {
    $code = $f.Code.Text
    if ($code -like '*ADDIN ZOTERO_ITEM*') { $items++ }
    elseif ($code -like '*ADDIN ZOTERO_BIBL*') { $bibl++ }
  }
  $pages = $doc.ComputeStatistics(2)
  if ($env:ZWLC_PDF) { $doc.ExportAsFixedFormat($env:ZWLC_PDF, 17) }
  $out = @{ ok = $true; wordVersion = $word.Version; fields = $total; zoteroItemFields = $items;
            zoteroBibliographyFields = $bibl; pages = $pages }
  $out | ConvertTo-Json -Compress
} catch {
  @{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json -Compress
} finally {
  if ($doc) { $doc.Close(0) | Out-Null }
  if ($word) { $word.Quit(0) | Out-Null }
}
"""


def find_word() -> str | None:
    if os.name != "nt":
        return None
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
        for sub in ("Microsoft Office\\root\\Office16", "Microsoft Office\\Office16",
                    "Microsoft Office\\root\\Office15", "Microsoft Office\\Office15"):
            exe = Path(base) / sub / "WINWORD.EXE"
            if exe.is_file():
                return str(exe)
    return None


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--pdf", type=Path, help="write a PDF here")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    src = args.docx.expanduser().resolve()
    if not src.is_file():
        print(f"ERROR: not found: {src}", file=sys.stderr)
        return EXIT_USAGE
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if os.name != "nt" or not powershell or not find_word():
        dump_json({"ok": False, "error": "Microsoft Word (Windows) not available; visual check skipped"})
        return EXIT_USAGE

    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "render-copy.docx"
        shutil.copy2(src, copy)
        env = dict(os.environ, ZWLC_DOCX=str(copy),
                   ZWLC_PDF=str(args.pdf.expanduser().resolve()) if args.pdf else "")
        if args.pdf:
            args.pdf.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
                                  capture_output=True, env=env, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            dump_json({"ok": False, "error": f"Word did not finish within {args.timeout}s"})
            return EXIT_FAIL
    text = proc.stdout.decode("utf-8", errors="replace").strip().splitlines()
    try:
        result = json.loads(text[-1]) if text else {"ok": False, "error": proc.stderr.decode(errors="replace")}
    except json.JSONDecodeError:
        result = {"ok": False, "error": "\n".join(text)[-500:]}
    result["document"] = str(src)
    if args.pdf and result.get("ok"):
        result["pdf"] = str(args.pdf.expanduser().resolve())
    dump_json(result)
    return EXIT_OK if result.get("ok") else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
