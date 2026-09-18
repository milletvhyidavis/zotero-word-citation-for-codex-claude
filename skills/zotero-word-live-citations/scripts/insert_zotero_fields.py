#!/usr/bin/env python3
"""Insert live Zotero citation / bibliography fields into an existing DOCX.

Writes a NEW file (default <stem>-zotero-cited.docx); the input is never
modified. Only word/document.xml, docProps/custom.xml, [Content_Types].xml and
_rels/.rels are touched, by targeted string edits - every other part, namespace
prefix and unknown Word extension is copied byte-for-byte.

Citation locations come from either
  --placements placements.json   explicit anchors (reproducible, preferred), or
  --placeholders                 in-text markers such as [@ref:C4; @ref:C5],
                                 [@zotero:ABCD1234] or [@doi:10.1000/xyz]

Items come from --items reference-map.json (resolve_references.py); a Zotero
key that is not in the map is fetched read-only from the local API.

placements.json:
  {"placements": [
     {"anchor": "required for mechanotransduction",   # text the citation follows
      "refs": ["C4", "C5"],             # refIds in the map ...
      "keys": ["ABCD1234"],             # ... and/or Zotero keys
      "paragraph": 12,                  # optional: 0-based paragraph index
      "paragraphContains": "...",       # optional: disambiguate the paragraph
      "occurrence": 1,                  # optional: which match (required if >1)
      "position": "after"}],            # or "before"
   "bibliography": {"heading": "References"}}     # optional

Use --list-paragraphs to print the paragraph index/text map first.

Each location gets exactly one field with a unique citationID; several items
at one location share that field. Visible text is provisional - Zotero Refresh
in Word replaces it. formattedCitation/plainCitation are never synthesized.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import shutil
import string
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_BASE_URL, EXIT_FAIL, EXIT_OK, EXIT_USAGE, NON_CITABLE_TYPES, UsageError,
    ZoteroLocal, dump_json, item_uri, load_json, normalize_doi, sha256_file, utf8_stdio,
    zotero_item_summary,
)
import validate_zotero_docx as validator  # noqa: E402

CSL_SCHEMA = "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"
CUSTOM_PROPS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
CUSTOM_PROPS_CT = "application/vnd.openxmlformats-officedocument.custom-properties+xml"
PROPS_FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"
STYLE_ALIASES = {
    "vancouver": "http://www.zotero.org/styles/vancouver",
    "apa": "http://www.zotero.org/styles/apa",
    "nature": "http://www.zotero.org/styles/nature",
    "ieee": "http://www.zotero.org/styles/ieee",
    "ama": "http://www.zotero.org/styles/american-medical-association",
    "chicago-author-date": "http://www.zotero.org/styles/chicago-author-date",
    "harvard": "http://www.zotero.org/styles/harvard-cite-them-right",
    "gb-t-7714-numeric": "http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-numeric",
    "gb-t-7714-author-date": "http://www.zotero.org/styles/china-national-standard-gb-t-7714-2015-author-date",
}
AUTHOR_DATE_HINTS = ("apa", "author-date", "harvard", "chicago-author")

RUN_RE = re.compile(r"<w:r(?:\s[^>]*)?>.*?</w:r>", re.S)
RUN_OPEN_RE = re.compile(r"<w:r(?:\s[^>]*)?>")
RPR_RE = re.compile(r"<w:rPr(?:\s[^>]*)?>.*?</w:rPr>|<w:rPr\s*/>", re.S)
T_RE = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:t(?:\s[^>]*)?/>", re.S)
FLDCHAR_RE = re.compile(r"<w:fldChar\b[^>]*w:fldCharType=\"(begin|separate|end)\"")
TOKEN_RE = re.compile(r"<w:fldChar\b[^>]*w:fldCharType=\"(begin|separate|end)\"[^>]*>|"
                      r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:t(?:\s[^>]*)?/>", re.S)
PARA_TAG_RE = re.compile(r"<w:p(?=[\s>/])[^>]*?(/?)>|</w:p>")
FLDSIMPLE_RE = re.compile(r"<w:fldSimple\b.*?</w:fldSimple>", re.S)
PLACEHOLDER_RE = re.compile(r"\[\s*(@(?:zotero|ref|doi|key):[^\]]+?)\s*\]")


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def xml_attr_escape(text: str) -> str:
    return xml_escape(text).replace('"', "&quot;")


def new_id(existing: set[str], n: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(random.choice(alphabet) for _ in range(n))
        if value not in existing:
            existing.add(value)
            return value


# ----------------------------------------------------------- paragraphs ----

@dataclass
class Para:
    index: int
    start: int
    end: int
    depth0: int  # complex-field nesting depth at paragraph start


def find_paragraphs(doc: str) -> list[Para]:
    """Innermost <w:p> elements in document order, with field depth at start."""
    stack: list[list[Any]] = []
    spans: list[tuple[int, int]] = []
    for m in PARA_TAG_RE.finditer(doc):
        if m.group(0).startswith("</"):
            if stack:
                start, has_child = stack.pop()
                if not has_child:
                    spans.append((start, m.end()))
                if stack:
                    stack[-1][1] = True
        elif m.group(1) == "/":
            if stack:
                stack[-1][1] = True
            spans.append((m.start(), m.end()))
        else:
            stack.append([m.start(), False])
    spans.sort()
    paras, depth, cursor = [], 0, 0
    for i, (s, e) in enumerate(spans):
        for fm in FLDCHAR_RE.finditer(doc, cursor, s):
            depth = depth + 1 if fm.group(1) == "begin" else depth - (fm.group(1) == "end")
        paras.append(Para(i, s, e, max(depth, 0)))
        for fm in FLDCHAR_RE.finditer(doc, s, e):
            depth = depth + 1 if fm.group(1) == "begin" else depth - (fm.group(1) == "end")
        cursor = e
    return paras


@dataclass
class Seg:
    run_start: int
    run_end: int
    t_start: int
    t_end: int
    text: str
    start: int  # offset in paragraph text

    @property
    def end(self) -> int:
        return self.start + len(self.text)


def segments(p: str, depth0: int) -> list[Seg]:
    """Editable text segments (w:t outside any field) of one paragraph."""
    locked = [(m.start(), m.end()) for m in FLDSIMPLE_RE.finditer(p)]
    segs: list[Seg] = []
    depth, offset = depth0, 0
    for rm in RUN_RE.finditer(p):
        in_simple = any(a <= rm.start() < b for a, b in locked)
        for tm in TOKEN_RE.finditer(p, rm.start(), rm.end()):
            if tm.group(1):
                depth = depth + 1 if tm.group(1) == "begin" else depth - (tm.group(1) == "end")
                continue
            text = html.unescape(tm.group(2) or "")
            if depth > 0 or in_simple or not text:
                continue
            segs.append(Seg(rm.start(), rm.end(), tm.start(), tm.end(), text, offset))
            offset += len(text)
    return segs


def para_text(p: str, depth0: int) -> str:
    return "".join(s.text for s in segments(p, depth0))


def run_parts(run: str) -> tuple[str, str]:
    """(open tag, rPr) of a run."""
    open_tag = RUN_OPEN_RE.match(run).group(0)
    rest = run[len(open_tag):]
    rpr = RPR_RE.match(rest)
    return open_tag, rpr.group(0) if rpr else ""


def t_elem(text: str) -> str:
    return f'<w:t xml:space="preserve">{xml_escape(text)}</w:t>'


def split_at(p: str, depth0: int, offset: int) -> tuple[str, int, str]:
    """Make a run boundary at text offset. Returns (paragraph, insert position, rPr)."""
    segs = segments(p, depth0)
    if not segs:
        pos = p.rfind("</w:p>")
        if pos < 0:
            raise UsageError("cannot insert into an empty self-closing paragraph")
        return p, pos, ""
    if offset <= 0:
        s0 = segs[0]
        return p, s0.run_start, run_parts(p[s0.run_start:s0.run_end])[1]
    seg = next((s for s in segs if s.start < offset <= s.end), None)
    if seg is None:
        raise UsageError(f"offset {offset} beyond paragraph text")
    run = p[seg.run_start:seg.run_end]
    open_tag, rpr = run_parts(run)
    inner_start = seg.run_start + len(open_tag) + len(rpr)
    inner_end = seg.run_end - len("</w:r>")
    local = offset - seg.start
    before = p[inner_start:seg.t_start] + (t_elem(seg.text[:local]) if local else "")
    after = (t_elem(seg.text[local:]) if local < len(seg.text) else "") + p[seg.t_end:inner_end]
    left = open_tag + rpr + before + "</w:r>" if before else ""
    right = open_tag + rpr + after + "</w:r>" if after else ""
    new_p = p[:seg.run_start] + left + right + p[seg.run_end:]
    return new_p, seg.run_start + len(left), rpr


def delete_range(p: str, depth0: int, start: int, end: int) -> str:
    p = split_at(p, depth0, end)[0]
    p = split_at(p, depth0, start)[0]
    for seg in sorted(segments(p, depth0), key=lambda s: s.t_start, reverse=True):
        if seg.start >= start and seg.end <= end:
            run = p[seg.run_start:seg.run_end]
            open_tag, rpr = run_parts(run)
            local_t = (seg.t_start - seg.run_start, seg.t_end - seg.run_start)
            new_run = run[:local_t[0]] + run[local_t[1]:]
            if new_run == open_tag + rpr + "</w:r>":
                new_run = ""
            p = p[:seg.run_start] + new_run + p[seg.run_end:]
    return p


# ---------------------------------------------------------------- fields ----

def field_runs(rpr: str, instruction: str, visible: str) -> str:
    r = f"<w:r>{rpr}"
    return (f'{r}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'{r}<w:instrText xml:space="preserve">{xml_escape(instruction)}</w:instrText></w:r>'
            f'{r}<w:fldChar w:fldCharType="separate"/></w:r>'
            f"{r}{t_elem(visible)}</w:r>"
            f'{r}<w:fldChar w:fldCharType="end"/></w:r>')


def citation_json(citation_id: str, items: list[dict[str, Any]], note_index: int) -> str:
    data = {
        "citationID": citation_id,
        "properties": {"noteIndex": note_index},
        "citationItems": [{"id": it["key"], "uris": [it["uri"]], "itemData": it["itemData"]}
                          for it in items],
        "schema": CSL_SCHEMA,
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def author_year_label(item_data: dict[str, Any]) -> str:
    authors = item_data.get("author") or []
    name = (authors[0].get("family") or authors[0].get("literal") or "Anon") if authors else "Anon"
    if len(authors) == 2:
        name += f" & {authors[1].get('family') or authors[1].get('literal') or ''}"
    elif len(authors) > 2:
        name += " et al."
    parts = ((item_data.get("issued") or {}).get("date-parts") or [[""]])[0]
    return f"{name}, {parts[0] if parts else 'n.d.'}"


def numeric_label(numbers: list[int]) -> str:
    numbers = sorted(set(numbers))
    out, i = [], 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        out.append(f"{numbers[i]}–{numbers[j]}" if j - i >= 2 else
                   ",".join(str(n) for n in numbers[i:j + 1]))
        i = j + 1
    return "[" + ",".join(out) + "]"


def bib_entry(n: int, d: dict[str, Any], numeric: bool) -> str:
    names = []
    for a in (d.get("author") or [])[:6]:
        if a.get("literal"):
            names.append(a["literal"])
        else:
            initials = "".join(w[0] for w in re.split(r"[\s\-.]+", a.get("given") or "") if w)
            names.append(f"{a.get('family', '')} {initials}".strip())
    if len(d.get("author") or []) > 6:
        names.append("et al")
    year = ((d.get("issued") or {}).get("date-parts") or [[""]])[0][0]
    tail = f"{d.get('container-title', '')}. {year}"
    if d.get("volume"):
        tail += f";{d['volume']}" + (f"({d['issue']})" if d.get("issue") else "")
    if d.get("page"):
        tail += f":{d['page']}"
    text = f"{', '.join(names)}. {d.get('title', '')}. {tail}."
    return (f"{n}. " if numeric else "") + re.sub(r"\s+", " ", text).replace(". .", ".")


# ----------------------------------------------------------- doc prefs ----

def prefs_xml(style_id: str, locale: str, note_type: int, zotero_version: str) -> str:
    session = new_id(set())
    return (f'<data data-version="3" zotero-version="{xml_attr_escape(zotero_version)}">'
            f'<session id="{session}"/>'
            f'<style id="{xml_attr_escape(style_id)}" locale="{xml_attr_escape(locale)}" '
            f'hasBibliography="1" bibliographyStyleHasBeenSet="1"/>'
            f'<prefs><pref name="fieldType" value="Field"/>'
            f'<pref name="automaticJournalAbbreviations" value="true"/>'
            f'<pref name="noteType" value="{note_type}"/></prefs></data>')


def apply_prefs(parts: dict[str, bytes], prefs: str) -> str:
    """Add ZOTERO_PREF_n custom properties unless the document already has them."""
    chunks = [prefs[i:i + 255] for i in range(0, len(prefs), 255)]
    custom = parts.get("docProps/custom.xml")
    if custom is not None:
        text = custom.decode("utf-8")
        if "ZOTERO_PREF_" in text:
            return "kept-existing"
        pids = [int(x) for x in re.findall(r'\bpid="(\d+)"', text)] or [1]
        pid = max(pids) + 1
        props = ""
        for i, chunk in enumerate(chunks, 1):
            props += (f'<property fmtid="{PROPS_FMTID}" pid="{pid}" name="ZOTERO_PREF_{i}">'
                      f"<vt:lpwstr>{xml_escape(chunk)}</vt:lpwstr></property>")
            pid += 1
        if "</Properties>" not in text:
            raise UsageError("docProps/custom.xml has an unexpected structure")
        prefix = re.search(r"<(\w+:)?Properties\b", text).group(1) or ""
        if prefix:
            props = props.replace("<property", f"<{prefix}property").replace(
                "</property>", f"</{prefix}property>")
        text = text.replace(f"</{prefix}Properties>", props + f"</{prefix}Properties>")
        parts["docProps/custom.xml"] = text.encode("utf-8")
        return "added"
    props = "".join(
        f'<property fmtid="{PROPS_FMTID}" pid="{i + 1}" name="ZOTERO_PREF_{i}">'
        f"<vt:lpwstr>{xml_escape(chunk)}</vt:lpwstr></property>"
        for i, chunk in enumerate(chunks, 1))
    parts["docProps/custom.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        f"{props}</Properties>").encode("utf-8")
    ct = parts["[Content_Types].xml"].decode("utf-8")
    if "/docProps/custom.xml" not in ct:
        ct = ct.replace("</Types>", f'<Override PartName="/docProps/custom.xml" '
                                    f'ContentType="{CUSTOM_PROPS_CT}"/></Types>')
        parts["[Content_Types].xml"] = ct.encode("utf-8")
    rels = parts["_rels/.rels"].decode("utf-8")
    if CUSTOM_PROPS_REL not in rels:
        ids = set(re.findall(r'\bId="([^"]+)"', rels))
        rid = next(f"rId{n}" for n in range(1, 10000) if f"rId{n}" not in ids)
        rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="{CUSTOM_PROPS_REL}" '
                                                f'Target="docProps/custom.xml"/></Relationships>')
        parts["_rels/.rels"] = rels.encode("utf-8")
    return "added"


# ------------------------------------------------------------ item pool ----

class ItemPool:
    def __init__(self, ref_map: dict[str, Any] | None, base_url: str):
        self.by_ref = dict((ref_map or {}).get("resolved", {}))
        self.by_key = {v["key"]: v for v in self.by_ref.values()}
        self.by_doi = {normalize_doi(v.get("doi") or (v.get("itemData") or {}).get("DOI")): v
                       for v in self.by_ref.values()}
        self.base_url = base_url
        self._z: ZoteroLocal | None = None

    def _fetch_key(self, key: str) -> dict[str, Any]:
        self._z = self._z or ZoteroLocal(self.base_url)
        try:
            item = self._z.item(key)
        except ConnectionError as exc:
            raise UsageError(f"Zotero key {key} not in --items map and not fetchable: {exc}")
        summary = zotero_item_summary(item)
        if summary["itemType"] in NON_CITABLE_TYPES or summary["parentItem"]:
            raise UsageError(f"{key} is a {summary['itemType']} (not a citable parent item)")
        entry = {"key": key, "uri": item_uri(item), "itemData": self._z.csljson(key),
                 "title": summary["title"], "matchMethod": "manual"}
        self.by_key[key] = entry
        return entry

    def get(self, kind: str, value: str) -> dict[str, Any]:
        value = value.strip()
        if kind == "ref":
            if value not in self.by_ref:
                raise UsageError(f"refId {value} is not resolved in --items map "
                                 "(missing/ambiguous refs cannot be cited)")
            return self.by_ref[value]
        if kind in ("zotero", "key"):
            return self.by_key.get(value) or self._fetch_key(value)
        if kind == "doi":
            doi = normalize_doi(value)
            if doi not in self.by_doi:
                raise UsageError(f"DOI {value} is not resolved in --items map")
            return self.by_doi[doi]
        raise UsageError(f"unknown reference kind {kind}")


def parse_placeholder(body: str) -> list[tuple[str, str]]:
    out = []
    for token in re.split(r"\s*;\s*", body):
        m = re.fullmatch(r"@(zotero|ref|doi|key):(.+)", token.strip())
        if not m:
            raise UsageError(f"bad placeholder token: {token!r}")
        out.append((m.group(1), m.group(2).strip()))
    return out


def anchor_pattern(anchor: str) -> re.Pattern[str]:
    quotes = {"'": "['‘’]", '"': "[\"“”]"}
    parts = []
    for ch in anchor.strip():
        if ch.isspace():
            if not parts or parts[-1] != r"\s+":
                parts.append(r"\s+")
        else:
            parts.append(quotes.get(ch, re.escape(ch)))
    return re.compile("".join(parts))


# ------------------------------------------------------------------ main ----

def plan_placements(doc: str, paras: list[Para], spec: list[dict[str, Any]], pool: ItemPool
                    ) -> list[dict[str, Any]]:
    ops = []
    for n, pl in enumerate(spec, 1):
        label = pl.get("id") or f"P{n}"
        anchor = pl.get("anchor")
        if not anchor:
            raise UsageError(f"{label}: 'anchor' is required")
        items = [pool.get("ref", r) for r in pl.get("refs", [])] + \
                [pool.get("key", k) for k in pl.get("keys", [])]
        if not items:
            raise UsageError(f"{label}: no refs/keys")
        if int(pl.get("noteIndex", 0)) != 0:
            raise UsageError(f"{label}: footnote/endnote citations are not supported yet (noteIndex must be 0)")
        candidates = paras
        if pl.get("paragraph") is not None:
            candidates = [p for p in paras if p.index == int(pl["paragraph"])]
        if pl.get("paragraphContains"):
            pat = anchor_pattern(pl["paragraphContains"])
            candidates = [p for p in candidates if pat.search(para_text(doc[p.start:p.end], p.depth0))]
        pat = anchor_pattern(anchor)
        hits = []
        for p in candidates:
            text = para_text(doc[p.start:p.end], p.depth0)
            hits += [(p, m) for m in pat.finditer(text)]
        occurrence = pl.get("occurrence")
        if not hits:
            raise UsageError(f"{label}: anchor not found: {anchor!r}")
        if len(hits) > 1 and occurrence is None:
            where = ", ".join(str(p.index) for p, _ in hits[:10])
            raise UsageError(f"{label}: anchor matches {len(hits)} places (paragraphs {where}); "
                             "add 'occurrence', 'paragraph' or 'paragraphContains'")
        k = int(occurrence or 1)
        if not 1 <= k <= len(hits):
            raise UsageError(f"{label}: occurrence {k} out of range (1..{len(hits)})")
        p, m = hits[k - 1]
        offset = m.end() if pl.get("position", "after") == "after" else m.start()
        text = para_text(doc[p.start:p.end], p.depth0)
        ops.append({"label": label, "para": p, "offset": offset, "delete": 0, "items": items,
                    "context": text[max(0, offset - 50):offset] + " <<CITE>> " + text[offset:offset + 30],
                    "spaceBefore": pl.get("spaceBefore")})
    return ops


def plan_placeholders(doc: str, paras: list[Para], pool: ItemPool) -> list[dict[str, Any]]:
    ops = []
    for p in paras:
        text = para_text(doc[p.start:p.end], p.depth0)
        for m in PLACEHOLDER_RE.finditer(text):
            items = [pool.get(kind, value) for kind, value in parse_placeholder(m.group(1))]
            ops.append({"label": m.group(0), "para": p, "offset": m.start(),
                        "delete": m.end() - m.start(), "items": items,
                        "context": text[max(0, m.start() - 50):m.start()] + " <<CITE>>",
                        "spaceBefore": False})
    return ops


def existing_citations(doc: str) -> tuple[set[str], list[tuple[int, list[str]]], bool]:
    ids, fields = set(), []
    for m in re.finditer(r"ADDIN ZOTERO_ITEM CSL_CITATION\s*(\{.*?\})\s*</w:instrText>", doc, re.S):
        try:
            data = json.loads(html.unescape(m.group(1)))
        except json.JSONDecodeError:
            continue
        ids.add(str(data.get("citationID")))
        fields.append((m.start(), [u for it in data.get("citationItems", []) for u in it.get("uris", [])[:1]]))
    return ids, fields, "ADDIN ZOTERO_BIBL" in doc


def build(args: argparse.Namespace) -> dict[str, Any]:
    src = args.input.expanduser().resolve()
    out = (args.output or src.with_name(f"{src.stem}-zotero-cited.docx")).expanduser().resolve()
    if not src.is_file():
        raise UsageError(f"input not found: {src}")
    if src == out:
        raise UsageError("output must differ from input (refusing to overwrite the original)")
    if out.exists() and not args.force:
        raise UsageError(f"output exists: {out} (use --force to replace it)")
    if not args.placements and not args.placeholders and not args.list_paragraphs \
            and not args.bibliography_heading:
        raise UsageError("give --placements and/or --placeholders (or --list-paragraphs)")

    input_hash = sha256_file(src)
    with zipfile.ZipFile(src) as z:
        infos = z.infolist()
        parts = {i.filename: z.read(i.filename) for i in infos}
    doc = parts["word/document.xml"].decode("utf-8")
    paras = find_paragraphs(doc)

    if args.list_paragraphs:
        return {"paragraphs": [{"index": p.index, "text": para_text(doc[p.start:p.end], p.depth0)}
                               for p in paras]}

    baseline = validator.inspect_docx(src)
    if baseline["errors"]:
        raise UsageError("input DOCX fails validation; fix it first: " + "; ".join(baseline["errors"][:5]))

    ref_map = load_json(args.items) if args.items else None
    pool = ItemPool(ref_map, args.base_url)
    spec = load_json(args.placements) if args.placements else {}
    ops = plan_placements(doc, paras, spec.get("placements", []), pool) if args.placements else []
    if args.placeholders:
        ops += plan_placeholders(doc, paras, pool)
    bib_spec = dict(spec.get("bibliography") or {})
    if args.bibliography_heading:
        bib_spec["heading"] = args.bibliography_heading
    if args.no_bibliography:
        bib_spec = {}

    seen = {(o["para"].index, o["offset"]) for o in ops}
    if len(seen) != len(ops):
        raise UsageError("two citations target the same location - merge them into one placement")

    style_id = STYLE_ALIASES.get(args.style, args.style)
    author_date = args.visible == "author-date" or (
        args.visible == "auto" and any(h in style_id for h in AUTHOR_DATE_HINTS))

    existing_ids, existing_fields, has_bibl = existing_citations(doc)
    # provisional numbering in document order over existing + new citations
    def text_position(pos: int) -> tuple[int, int]:
        p = next((p for p in paras if p.start <= pos < p.end), None)
        if p is None:
            return (pos, 0)
        segs = segments(doc[p.start:p.end], p.depth0)
        return (p.start, sum(len(s.text) for s in segs if s.t_start < pos - p.start))

    order = sorted([(text_position(pos), uris) for pos, uris in existing_fields] +
                   [((o["para"].start, o["offset"]), [it["uri"] for it in o["items"]]) for o in ops],
                   key=lambda x: x[0])
    numbers: dict[str, int] = {}
    for _, uris in order:
        for u in uris:
            numbers.setdefault(u, len(numbers) + 1)

    audit = []
    edits_by_para: dict[int, list[dict[str, Any]]] = {}
    for o in ops:
        cid = new_id(existing_ids)
        o["citationID"] = cid
        if author_date:
            visible = "(" + "; ".join(author_year_label(it["itemData"]) for it in o["items"]) + ")"
        else:
            visible = numeric_label([numbers[it["uri"]] for it in o["items"]])
        o["visible"] = visible
        o["instruction"] = f" ADDIN ZOTERO_ITEM CSL_CITATION {citation_json(cid, o['items'], 0)} "
        space = o["spaceBefore"] if o["spaceBefore"] is not None else author_date
        o["space"] = bool(space) and o["delete"] == 0
        edits_by_para.setdefault(o["para"].index, []).append(o)
        audit.append({"placement": o["label"], "paragraph": o["para"].index, "citationID": cid,
                      "keys": [it["key"] for it in o["items"]], "visibleText": visible,
                      "context": o["context"]})

    # apply edits paragraph by paragraph, last paragraph first
    for p in sorted(paras, key=lambda x: x.start, reverse=True):
        if p.index not in edits_by_para:
            continue
        px = doc[p.start:p.end]
        for o in sorted(edits_by_para[p.index], key=lambda x: x["offset"], reverse=True):
            if o["delete"]:
                px = delete_range(px, p.depth0, o["offset"], o["offset"] + o["delete"])
            px, pos, rpr = split_at(px, p.depth0, o["offset"])
            runs = field_runs(rpr, o["instruction"], o["visible"])
            if o["space"]:
                runs = f"<w:r>{rpr}{t_elem(' ')}</w:r>" + runs
            px = px[:pos] + runs + px[pos:]
        doc = doc[:p.start] + px + doc[p.end:]

    # bibliography
    bibliography = "none"
    if bib_spec:
        if has_bibl:
            bibliography = "kept-existing"
        else:
            cited = {}
            for o in sorted(ops, key=lambda x: (x["para"].start, x["offset"])):
                for it in o["items"]:
                    cited.setdefault(it["uri"], it)
            ordered = sorted(cited.values(), key=lambda it: numbers[it["uri"]]) if not author_date else \
                sorted(cited.values(), key=lambda it: author_year_label(it["itemData"]))
            entries = [bib_entry(numbers[it["uri"]], it["itemData"], not author_date) for it in ordered] \
                or ["{Bibliography}"]
            instr = ' ADDIN ZOTERO_BIBL {"uncited":[],"omitted":[],"custom":[]} CSL_BIBLIOGRAPHY '
            paras_xml = []
            for i, entry in enumerate(entries):
                runs = ""
                if i == 0:
                    runs += ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                             f'<w:r><w:instrText xml:space="preserve">{xml_escape(instr)}</w:instrText></w:r>'
                             '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
                runs += f"<w:r>{t_elem(entry)}</w:r>"
                if i == len(entries) - 1:
                    runs += '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
                paras_xml.append(f"<w:p>{runs}</w:p>")
            block = "".join(paras_xml)
            paras = find_paragraphs(doc)
            heading = bib_spec.get("heading")
            target = None
            if heading:
                hp = anchor_pattern(heading)
                target = next((p for p in paras if hp.fullmatch(
                    para_text(doc[p.start:p.end], p.depth0).strip())), None)
            if target is not None:
                doc = doc[:target.end] + block + doc[target.end:]
                bibliography = f"added after heading '{heading}'"
            else:
                head = f"<w:p><w:r><w:rPr><w:b/></w:rPr>{t_elem(heading)}</w:r></w:p>" if heading else ""
                body_end = doc.rfind("<w:sectPr")
                body_close = doc.rfind("</w:body>")
                pos = body_end if 0 <= body_end > doc.rfind("</w:p>") else body_close
                doc = doc[:pos] + head + block + doc[pos:]
                bibliography = "added at end" + (f" with new heading '{heading}'" if heading else "")

    parts["word/document.xml"] = doc.encode("utf-8")

    zotero_version = args.zotero_version
    if not zotero_version:
        status = ZoteroLocal(args.base_url, timeout=3).request("/connector/ping", timeout=3)
        zotero_version = status.headers.get("X-Zotero-Version") or "7.0"
    prefs_state = apply_prefs(parts, prefs_xml(style_id, args.locale, args.note_type, zotero_version))

    if args.dry_run:
        return {"dryRun": True, "placements": audit, "bibliography": bibliography}

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=out.parent, suffix=".tmp") as tmp:
        tmp_path = Path(tmp.name)
    try:
        with zipfile.ZipFile(tmp_path, "w") as zout:
            written = set()
            for info in infos:
                zout.writestr(info, parts[info.filename])
                written.add(info.filename)
            for name, data in parts.items():
                if name not in written:
                    zout.writestr(zipfile.ZipInfo(name, date_time=infos[0].date_time), data,
                                  compress_type=zipfile.ZIP_DEFLATED)
        shutil.move(str(tmp_path), out)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    vargs = validator.build_parser().parse_args(
        [str(out), "--baseline", str(src), "--expected-increase", str(len(ops)),
         "--require-item-data"]
        + (["--preserve-baseline-citations"] if baseline["zoteroFields"] else [])
        + (["--expect-bibliography"] if bib_spec else []))
    result = validator.validate(vargs)
    port = result["portability"]
    return {
        "inputDocument": str(src),
        "outputDocument": str(out),
        "inputSHA256": input_hash,
        "outputSHA256": sha256_file(out),
        "inputUnchanged": sha256_file(src) == input_hash,
        "fieldsInserted": len(ops),
        "zoteroFieldsTotal": result["zoteroFieldCount"],
        "citationItemOccurrences": result["citationItemOccurrences"],
        "uniqueItems": result["uniqueItemURIs"],
        "embeddedItemData": f"{port['itemsWithEmbeddedData']}/{port['citationItemCount']}",
        "libraryNamespaces": port["libraryNamespaces"],
        "bibliography": bibliography,
        "documentPreferences": prefs_state,
        "style": style_id,
        "structuralValidation": "passed" if result["valid"] else "failed",
        "validationErrors": result["errors"],
        "validationWarnings": result["warnings"],
        "placements": audit,
    }


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="default: <stem>-zotero-cited.docx next to input")
    parser.add_argument("--items", type=Path, help="reference-map.json from resolve_references.py")
    parser.add_argument("--placements", type=Path, help="placements JSON (see above)")
    parser.add_argument("--placeholders", action="store_true",
                        help="replace [@ref:..]/[@zotero:..]/[@doi:..] markers in the text")
    parser.add_argument("--style", default="vancouver",
                        help="CSL style id or alias (%s); default %%(default)s"
                             % ", ".join(sorted(STYLE_ALIASES)))
    parser.add_argument("--locale", default="en-US", help="citation locale, e.g. en-US, zh-CN")
    parser.add_argument("--note-type", type=int, default=0, choices=(0, 1, 2),
                        help="0 in-text (default), 1 footnotes, 2 endnotes (document pref only)")
    parser.add_argument("--visible", choices=("auto", "numeric", "author-date"), default="auto",
                        help="provisional visible text format (Zotero Refresh replaces it)")
    parser.add_argument("--bibliography-heading",
                        help="insert a ZOTERO_BIBL field after the paragraph with exactly this text "
                             "(created at the end if absent)")
    parser.add_argument("--no-bibliography", action="store_true")
    parser.add_argument("--zotero-version", help="value for the prefs zotero-version attribute")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--list-paragraphs", action="store_true",
                        help="print paragraph index/text JSON and exit")
    parser.add_argument("--dry-run", action="store_true", help="plan and audit only")
    parser.add_argument("--force", action="store_true", help="replace an existing OUTPUT file")
    parser.add_argument("--report", type=Path, help="also write the JSON report here")
    args = parser.parse_args(argv)
    try:
        report = build(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    dump_json(report)
    if args.report:
        dump_json(report, args.report)
    return EXIT_OK if report.get("structuralValidation", "passed") == "passed" else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
