#!/usr/bin/env python3
"""Find candidate papers in public bibliographic databases (read-only, stdlib only).

Sources: Crossref, OpenAlex, PubMed (NCBI E-utilities). Results from several
sources are merged by DOI/PMID and written as a JSON list of *reference records*
- the same schema that resolve_references.py and build_import_file.py consume:

  {"refId", "title", "authors": [{"family","given"}|{"literal"}], "year",
   "journal", "volume", "issue", "pages", "doi", "pmid", "abstract", "url",
   "type", "sources": [...]}

Examples:
  search_literature.py search "Piezo2 cochlear hair cell mechanotransduction" \
      --source openalex,pubmed --limit 10 --from-year 2015 --out candidates.json
  search_literature.py lookup --doi 10.1038/nature13980 --pmid 25471886 --out refs.json

Every record the agent proposes to cite must come from this tool (or be looked
up with `lookup`) so that titles/DOIs are real, never invented.
Set $ZWLC_MAILTO (or --mailto) to your e-mail for polite API use; $NCBI_API_KEY
is used for PubMed when present.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    EXIT_FAIL, EXIT_OK, EXIT_USAGE, dump_json, http, normalize_doi, utf8_stdio, year_of,
)

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF_TYPES = {"journal-article": "article-journal", "proceedings-article": "paper-conference",
                  "book-chapter": "chapter", "book": "book", "posted-content": "article",
                  "dissertation": "thesis", "report": "report"}
OPENALEX_TYPES = {"article": "article-journal", "review": "article-journal", "book": "book",
                  "book-chapter": "chapter", "preprint": "article", "dissertation": "thesis",
                  "report": "report"}


def strip_tags(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip() or None


def record(**kw: Any) -> dict[str, Any]:
    base = {"refId": None, "title": None, "authors": [], "year": None, "journal": None,
            "volume": None, "issue": None, "pages": None, "doi": None, "pmid": None,
            "abstract": None, "url": None, "type": "article-journal", "sources": []}
    base.update({k: v for k, v in kw.items() if v not in (None, "", [])})
    return base


# ------------------------------------------------------------- parsers ----

def parse_crossref(message: dict[str, Any]) -> list[dict[str, Any]]:
    works = message.get("items") if "items" in message else [message]
    out = []
    for w in works or []:
        date = (w.get("issued") or {}).get("date-parts") or [[None]]
        authors = []
        for a in w.get("author") or []:
            if a.get("family"):
                authors.append({"family": a["family"], "given": a.get("given", "")})
            elif a.get("name"):
                authors.append({"literal": a["name"]})
        out.append(record(
            title=strip_tags((w.get("title") or [None])[0]),
            authors=authors,
            year=str(date[0][0]) if date and date[0] and date[0][0] else None,
            journal=(w.get("container-title") or [None])[0],
            volume=w.get("volume"), issue=w.get("issue"), pages=w.get("page"),
            doi=normalize_doi(w.get("DOI")), abstract=strip_tags(w.get("abstract")),
            url=w.get("URL"), type=CROSSREF_TYPES.get(w.get("type"), "article-journal"),
            sources=["crossref"]))
    return out


def openalex_abstract(inverted: dict[str, list[int]] | None) -> str | None:
    if not inverted:
        return None
    positions = [(pos, word) for word, poss in inverted.items() for pos in poss]
    return " ".join(word for _, word in sorted(positions)) or None


def parse_openalex(payload: dict[str, Any]) -> list[dict[str, Any]]:
    works = payload.get("results") if "results" in payload else [payload]
    out = []
    for w in works or []:
        ids = w.get("ids") or {}
        pmid = (ids.get("pmid") or "").rstrip("/").rsplit("/", 1)[-1] or None
        biblio = w.get("biblio") or {}
        pages = None
        if biblio.get("first_page"):
            pages = biblio["first_page"] + (f"-{biblio['last_page']}" if biblio.get("last_page")
                                            and biblio["last_page"] != biblio["first_page"] else "")
        source = ((w.get("primary_location") or {}).get("source") or {})
        authors = []
        for a in w.get("authorships") or []:
            name = (a.get("author") or {}).get("display_name") or a.get("raw_author_name")
            if not name:
                continue
            parts = name.rsplit(" ", 1)
            authors.append({"family": parts[-1], "given": parts[0] if len(parts) == 2 else ""})
        out.append(record(
            title=strip_tags(w.get("title") or w.get("display_name")), authors=authors,
            year=str(w["publication_year"]) if w.get("publication_year") else None,
            journal=source.get("display_name"), volume=biblio.get("volume"),
            issue=biblio.get("issue"), pages=pages, doi=normalize_doi(w.get("doi")),
            pmid=pmid if pmid and pmid.isdigit() else None,
            abstract=openalex_abstract(w.get("abstract_inverted_index")),
            url=w.get("doi") or w.get("id"),
            type=OPENALEX_TYPES.get(w.get("type"), "article-journal"),
            sources=["openalex"], citedByCount=w.get("cited_by_count")))
    return out


def parse_pubmed_xml(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    out = []
    for art in root.iter("PubmedArticle"):
        cit = art.find("MedlineCitation")
        a = cit.find("Article") if cit is not None else None
        if a is None:
            continue
        pmid = cit.findtext("PMID")
        journal = a.find("Journal")
        issue = journal.find("JournalIssue") if journal is not None else None
        year = None
        if issue is not None:
            year = year_of(issue.findtext("PubDate/Year") or issue.findtext("PubDate/MedlineDate"))
        authors = []
        for au in a.findall("AuthorList/Author"):
            if au.findtext("LastName"):
                authors.append({"family": au.findtext("LastName"),
                                "given": au.findtext("ForeName") or au.findtext("Initials") or ""})
            elif au.findtext("CollectiveName"):
                authors.append({"literal": au.findtext("CollectiveName")})
        doi = None
        for aid in art.findall("PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = normalize_doi(aid.text)
        if not doi:
            for eid in a.findall("ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = normalize_doi(eid.text)
        abstract = " ".join("".join(p.itertext()).strip() for p in a.findall("Abstract/AbstractText"))
        out.append(record(
            title="".join(a.find("ArticleTitle").itertext()).strip().rstrip(".")
            if a.find("ArticleTitle") is not None else None,
            authors=authors, year=year,
            journal=journal.findtext("Title") if journal is not None else None,
            volume=issue.findtext("Volume") if issue is not None else None,
            issue=issue.findtext("Issue") if issue is not None else None,
            pages=a.findtext("Pagination/MedlinePgn"), doi=doi, pmid=pmid,
            abstract=abstract or None,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            sources=["pubmed"]))
    return out


# ------------------------------------------------------------- fetchers ----

def _get(url: str, timeout: float) -> Any:
    resp = http(url, timeout=timeout)
    if resp.status == 429:
        time.sleep(2)
        resp = http(url, timeout=timeout)
    if not resp.ok:
        raise ConnectionError(f"{url.split('?')[0]}: status={resp.status} {resp.error or ''}")
    return resp


def crossref_search(q: str, limit: int, mailto: str | None, from_year: int | None,
                    timeout: float) -> list[dict[str, Any]]:
    params = {"query.bibliographic": q, "rows": limit}
    if from_year:
        params["filter"] = f"from-pub-date:{from_year}"
    if mailto:
        params["mailto"] = mailto
    return parse_crossref(_get(f"{CROSSREF}?{urllib.parse.urlencode(params)}", timeout).json()["message"])


def openalex_search(q: str, limit: int, mailto: str | None, from_year: int | None,
                    timeout: float) -> list[dict[str, Any]]:
    params = {"search": q, "per-page": limit}
    if from_year:
        params["filter"] = f"from_publication_date:{from_year}-01-01"
    if mailto:
        params["mailto"] = mailto
    return parse_openalex(_get(f"{OPENALEX}?{urllib.parse.urlencode(params)}", timeout).json())


def pubmed_fetch(pmids: list[str], timeout: float) -> list[dict[str, Any]]:
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    return parse_pubmed_xml(_get(f"{EUTILS}/efetch.fcgi?{urllib.parse.urlencode(params)}", timeout).text)


def pubmed_search(q: str, limit: int, mailto: str | None, from_year: int | None,
                  timeout: float) -> list[dict[str, Any]]:
    params = {"db": "pubmed", "term": q, "retmax": limit, "retmode": "json", "sort": "relevance"}
    if from_year:
        params.update({"datetype": "pdat", "mindate": str(from_year), "maxdate": "3000"})
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    ids = _get(f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}", timeout).json()
    return pubmed_fetch(ids.get("esearchresult", {}).get("idlist", []), timeout)


SEARCHERS = {"crossref": crossref_search, "openalex": openalex_search, "pubmed": pubmed_search}


def merge_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge records describing the same work (same DOI or PMID), keeping first-seen order."""
    merged: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}
    for rec in records:
        keys = [f"doi:{rec['doi']}"] if rec.get("doi") else []
        keys += [f"pmid:{rec['pmid']}"] if rec.get("pmid") else []
        target = next((index[k] for k in keys if k in index), None)
        if target is None:
            target = dict(rec)
            merged.append(target)
        else:
            for field, value in rec.items():
                if field == "sources":
                    target["sources"] = sorted(set(target["sources"]) | set(value))
                elif not target.get(field) and value:
                    target[field] = value
        for k in ([f"doi:{target['doi']}"] if target.get("doi") else []) + \
                 ([f"pmid:{target['pmid']}"] if target.get("pmid") else []):
            index[k] = target
    for n, rec in enumerate(merged, 1):
        rec["refId"] = rec.get("refId") or f"C{n}"
    return merged


def lookup(dois: list[str], pmids: list[str], mailto: str | None, timeout: float) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for raw in dois:
        doi = normalize_doi(raw)
        if not doi:
            raise ValueError(f"not a DOI: {raw}")
        url = f"{CROSSREF}/{urllib.parse.quote(doi)}" + (f"?mailto={urllib.parse.quote(mailto)}" if mailto else "")
        found.extend(parse_crossref(_get(url, timeout).json()["message"]))
    found.extend(pubmed_fetch([p for p in pmids if p.isdigit()], timeout))
    return merge_records(found)


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mailto", default=os.environ.get("ZWLC_MAILTO"),
                        help="contact e-mail sent to Crossref/OpenAlex (default $ZWLC_MAILTO)")
    parser.add_argument("--timeout", type=float, default=20)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search", help="keyword search")
    s.add_argument("query")
    s.add_argument("--source", default="openalex,pubmed",
                   help="comma list of crossref,openalex,pubmed (default %(default)s)")
    s.add_argument("--limit", type=int, default=10, help="results per source")
    s.add_argument("--from-year", type=int)
    s.add_argument("--out", help="write JSON here instead of stdout")
    s.add_argument("--brief", action="store_true", help="omit abstracts")
    lk = sub.add_parser("lookup", help="fetch canonical metadata for known DOIs/PMIDs")
    lk.add_argument("--doi", action="append", default=[])
    lk.add_argument("--pmid", action="append", default=[])
    lk.add_argument("--out")
    args = parser.parse_args(argv)

    try:
        if args.command == "lookup":
            if not args.doi and not args.pmid:
                parser.error("lookup needs --doi and/or --pmid")
            dump_json(lookup(args.doi, args.pmid, args.mailto, args.timeout), args.out)
            return EXIT_OK
        sources = [s.strip() for s in args.source.split(",") if s.strip()]
        unknown = set(sources) - set(SEARCHERS)
        if unknown:
            parser.error(f"unknown source(s): {', '.join(sorted(unknown))}")
        results: list[dict[str, Any]] = []
        failures = []
        for name in sources:
            try:
                results.extend(SEARCHERS[name](args.query, args.limit, args.mailto,
                                               args.from_year, args.timeout))
            except (ConnectionError, ValueError, KeyError, ET.ParseError) as exc:
                failures.append(f"{name}: {exc}")
                print(f"WARNING: {name} failed: {exc}", file=sys.stderr)
        merged = merge_records(results)
        if args.brief:
            for rec in merged:
                rec.pop("abstract", None)
        dump_json(merged, args.out)
        if args.out:
            print(f"{len(merged)} candidate(s) -> {args.out}", file=sys.stderr)
        return EXIT_FAIL if failures and not merged else EXIT_OK
    except (ConnectionError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_FAIL
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
