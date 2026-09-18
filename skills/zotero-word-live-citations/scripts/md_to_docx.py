#!/usr/bin/env python3
"""Convert a simple Markdown manuscript to a clean DOCX (stdlib only).

Supported: '#'..'######' headings (4-6 map to Heading3) (the first '#' becomes the Title), paragraphs,
'- ' / '* ' bullets, '1. ' numbered lines (kept as text), **bold**, *italic*,
and blank-line paragraph breaks. Citation markers such as [@ref:C3; @ref:C7]
are kept verbatim so insert_zotero_fields.py --placeholders can turn them into
live Zotero fields afterwards.

  md_to_docx.py --input review.md --output review.docx [--east-asia-font SimSun]
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import EXIT_OK, EXIT_USAGE, utf8_stdio  # noqa: E402

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_runs(text: str) -> str:
    runs = []
    for token in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not token:
            continue
        rpr = ""
        if token.startswith("**") and token.endswith("**"):
            token, rpr = token[2:-2], "<w:rPr><w:b/></w:rPr>"
        elif token.startswith("*") and token.endswith("*") and len(token) > 1:
            token, rpr = token[1:-1], "<w:rPr><w:i/></w:rPr>"
        runs.append(f'<w:r>{rpr}<w:t xml:space="preserve">{esc(token)}</w:t></w:r>')
    return "".join(runs)


def paragraph(text: str, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{inline_runs(text)}</w:p>"


def convert(md: str) -> str:
    body, buf, title_used = [], [], False

    def flush() -> None:
        if buf:
            body.append(paragraph(" ".join(s.strip() for s in buf)))
            buf.clear()

    for line in md.splitlines():
        stripped = line.strip()
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush()
            level = min(len(m.group(1)), 3)  # only Heading1-3 styles exist
            if level == 1 and not title_used:
                body.append(paragraph(m.group(2), "Title"))
                title_used = True
            else:
                body.append(paragraph(m.group(2), f"Heading{level}"))
        elif not stripped:
            flush()
        elif re.match(r"^[-*]\s+", stripped):
            flush()
            body.append(paragraph("• " + re.sub(r"^[-*]\s+", "", stripped), "ListParagraph"))
        else:
            buf.append(stripped)
    flush()
    return "".join(body)


def styles_xml(latin: str, east_asia: str) -> str:
    def style(sid: str, name: str, size: int, bold: bool, before: int, after: int, outline: int | None) -> str:
        ol = f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else ""
        b = "<w:b/>" if bold else ""
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
                f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:spacing w:before="{before}" w:after="{after}"/>{ol}</w:pPr>'
                f'<w:rPr>{b}<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:style>')
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W_NS}"><w:docDefaults><w:rPrDefault><w:rPr>'
        f'<w:rFonts w:ascii="{latin}" w:hAnsi="{latin}" w:eastAsia="{east_asia}" w:cs="{latin}"/>'
        f'<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr>'
        f'</w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/>'
        f'<w:jc w:val="both"/></w:pPr></w:pPrDefault></w:docDefaults>'
        f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
        + style("Title", "Title", 32, True, 240, 240, None).replace("<w:pPr>", '<w:pPr><w:jc w:val="center"/>', 1)
        + style("Heading1", "heading 1", 28, True, 240, 120, 0)
        + style("Heading2", "heading 2", 24, True, 200, 100, 1)
        + style("Heading3", "heading 3", 22, True, 160, 80, 2)
        + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/>'
          '<w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/></w:pPr></w:style>'
        + "</w:styles>")


def write_docx(body_xml: str, out: Path, latin: str, east_asia: str, title: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{W_NS}" '
                f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<w:body>{body_xml}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                f'<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
                f'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr></w:body></w:document>')
    files = {
        "[Content_Types].xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '</Types>',
        "_rels/.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '</Relationships>',
        "word/_rels/document.xml.rels":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>',
        "word/document.xml": document,
        "word/styles.xml": styles_xml(latin, east_asia),
        "docProps/core.xml":
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{esc(title)}</dc:title>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
            '</cp:coreProperties>',
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--latin-font", default="Times New Roman")
    parser.add_argument("--east-asia-font", default="SimSun")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output")
    args = parser.parse_args(argv)
    src, out = args.input.expanduser().resolve(), args.output.expanduser().resolve()
    if not src.is_file():
        print(f"ERROR: input not found: {src}", file=sys.stderr)
        return EXIT_USAGE
    if out.exists() and not args.force:
        print(f"ERROR: output exists: {out} (use --force)", file=sys.stderr)
        return EXIT_USAGE
    md = src.read_text(encoding="utf-8-sig")
    title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), src.stem)
    write_docx(convert(md), out, args.latin_font, args.east_asia_font, title)
    print(str(out))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
