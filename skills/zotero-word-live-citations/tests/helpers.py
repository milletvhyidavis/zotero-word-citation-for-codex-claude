"""Shared test helpers: tiny DOCX builders and a synthetic reference map."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SCHEMA = "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"


def item(key: str, title: str, year: int = 2020, ns: str = "users/111") -> dict:
    uri = f"http://zotero.org/{ns}/items/{key}"
    return {"key": key, "uri": uri, "title": title, "year": str(year), "matchMethod": "doi",
            "itemData": {"id": uri, "type": "article-journal", "title": title,
                         "author": [{"family": "Smith", "given": "Anna"}],
                         "container-title": "J Test", "issued": {"date-parts": [[year]]}}}


def ref_map(tmp: Path) -> Path:
    data = {"resolved": {"R1": item("AAAA1111", "First paper"),
                         "R2": item("BBBB2222", "Second paper", 2019),
                         "R3": item("CCCC3333", "Third paper", 2021)}}
    path = tmp / "map.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def run(text: str, bold: bool = False) -> str:
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f'<w:r w:rsidR="00AB12CD">{rpr}<w:t xml:space="preserve">{text}</w:t></w:r>'


def zotero_field(citation_id: str, key: str, visible: str = "[1]", ns: str = "users/111") -> str:
    uri = f"http://zotero.org/{ns}/items/{key}"
    data = {"citationID": citation_id, "properties": {"noteIndex": 0},
            "citationItems": [{"id": key, "uris": [uri], "itemData": {"id": uri, "type": "book", "title": key}}],
            "schema": SCHEMA}
    instr = (" ADDIN ZOTERO_ITEM CSL_CITATION " + json.dumps(data) + " ").replace("&", "&amp;") \
        .replace("<", "&lt;").replace(">", "&gt;")
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve">{instr}</w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r><w:t>{visible}</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def make_docx(path: Path, paragraphs: list[str], extra_parts: dict[str, str] | None = None,
              custom_xml: str | None = None) -> Path:
    """paragraphs: list of inner-XML strings for <w:p>."""
    body = "".join(f"<w:p>{p}</w:p>" for p in paragraphs)
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{W}" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
                f'<w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:body></w:document>')
    ct_extra = ('<Override PartName="/docProps/custom.xml" ContentType="application/'
                'vnd.openxmlformats-officedocument.custom-properties+xml"/>') if custom_xml else ""
    rel_extra = ('<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                 'relationships/custom-properties" Target="docProps/custom.xml"/>') if custom_xml else ""
    parts = {
        "[Content_Types].xml":
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
            f'officedocument.wordprocessingml.document.main+xml"/>{ct_extra}</Types>',
        "_rels/.rels":
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            f'officeDocument" Target="word/document.xml"/>{rel_extra}</Relationships>',
        "word/document.xml": document,
        "word/unknownExtension.xml": '<x:ext xmlns:x="urn:vendor">keep me</x:ext>',
    }
    if custom_xml:
        parts["docProps/custom.xml"] = custom_xml
    parts.update(extra_parts or {})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data)
    return path


def read_part(path: Path, name: str) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read(name).decode("utf-8")
