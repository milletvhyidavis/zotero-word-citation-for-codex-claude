#!/usr/bin/env python3
"""Environment self-test for the zotero-word-live-citations skill.

Checks (read-only; installs nothing, changes no Zotero setting, prints no
library contents):
  1. Python >= 3.9
  2. Zotero Desktop reachable on the local port (connector ping)
  3. 'Allow other applications to communicate' / local API enabled (/api/)
  4. Local API can list one item key
  5. Offline DOCX pipeline: build a DOCX, insert a synthetic field, validate it
  6. Microsoft Word present (visual rendering only)

Capabilities are reported separately: a missing Word only disables visual
rendering; a missing Zotero disables search/resolve/import but not validation.

  selftest.py [--strict] [--json] [--base-url URL]
--strict exits 1 unless Zotero is reachable and the offline pipeline passes.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def check_pipeline() -> tuple[bool, str]:
    import contextlib
    import io

    import insert_zotero_fields as ins
    import md_to_docx
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "selftest 测试.md"
        src.write_text("# T\n\nClaim one [@ref:R1].\n\n## References\n", encoding="utf-8")
        docx = tmp_path / "selftest 测试.docx"
        with contextlib.redirect_stdout(io.StringIO()):
            built = md_to_docx.main(["--input", str(src), "--output", str(docx)])
        if built != 0:
            return False, "md_to_docx failed"
        uri = "http://zotero.org/users/1/items/ABCD1234"
        ref_map = {"resolved": {"R1": {"key": "ABCD1234", "uri": uri, "title": "Selftest",
                                       "itemData": {"id": uri, "type": "article-journal",
                                                    "title": "Selftest",
                                                    "issued": {"date-parts": [[2020]]}}}}}
        (tmp_path / "map.json").write_text(json.dumps(ref_map), encoding="utf-8")
        report_path = tmp_path / "report.json"
        with contextlib.redirect_stdout(io.StringIO()):
            code = ins.main(["--input", str(docx), "--items", str(tmp_path / "map.json"),
                             "--placeholders", "--bibliography-heading", "References",
                             "--zotero-version", "selftest", "--report", str(report_path)])
        if code != 0:
            return False, f"insert_zotero_fields exit {code}"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        ok = report["structuralValidation"] == "passed" and report["fieldsInserted"] == 1
        return ok, "insert + validate OK" if ok else f"validation: {report['validationErrors']}"


def main(argv: list[str] | None = None) -> int:
    from _common import DEFAULT_BASE_URL, ZoteroLocal, utf8_stdio
    from word_render import find_word
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args(argv)

    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    add("python", sys.version_info >= (3, 9), f"{sys.version.split()[0]} at {sys.executable}")

    z = ZoteroLocal(args.base_url, timeout=3)
    ping = z.request("/connector/ping", timeout=3)
    add("zotero-running", ping.ok,
        f"Zotero {ping.headers.get('X-Zotero-Version')}" if ping.ok else
        f"not reachable at {args.base_url} ({ping.error}); start Zotero Desktop")
    api = z.request("/api/", timeout=3)
    add("zotero-local-api", api.ok,
        "local API enabled" if api.ok else
        "enable Zotero Settings > Advanced > 'Allow other applications on this computer "
        "to communicate with Zotero'")
    items = z.request("/api/users/0/items/top?limit=1&format=keys", timeout=5) if api.ok else None
    add("zotero-read-items", bool(items and items.ok),
        "read one item key" if items and items.ok else "cannot read items")

    try:
        ok, detail = check_pipeline()
    except Exception as exc:  # report, never crash
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    add("docx-pipeline", ok, detail)

    word = find_word()
    add("microsoft-word", bool(word), word or "not found - visual rendering unavailable (fields still work)")

    by = {c["check"]: c["ok"] for c in checks}
    capabilities = {
        "literatureSearch": True,
        "zoteroSearchResolve": bool(by["zotero-read-items"]),
        "zoteroImport": bool(by["zotero-running"]),
        "docxInsertValidate": bool(by["docx-pipeline"]),
        "markdownToDocx": bool(by["docx-pipeline"]),
        "wordRendering": bool(by["microsoft-word"]),
    }
    if args.json:
        print(json.dumps({"checks": checks, "capabilities": capabilities}, indent=2, ensure_ascii=False))
    else:
        for c in checks:
            print(f"[{'OK ' if c['ok'] else 'NO '}] {c['check']}: {c['detail']}")
        print("capabilities: " + ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in capabilities.items()))
    essential = by["python"] and by["docx-pipeline"]
    if args.strict:
        essential = essential and by["zotero-read-items"]
    return 0 if essential else 1


if __name__ == "__main__":
    raise SystemExit(main())
