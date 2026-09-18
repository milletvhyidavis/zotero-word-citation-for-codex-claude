# Literature search

`search_literature.py` queries public APIs with the standard library only:

| Source | Endpoint | Strength |
|---|---|---|
| `openalex` | api.openalex.org/works?search= | broad, abstracts, citation counts |
| `pubmed` | eutils esearch + efetch (XML) | biomedicine, PMIDs, MeSH-quality metadata |
| `crossref` | api.crossref.org/works?query.bibliographic= | DOI registry, all disciplines, good for `lookup` |

Output record schema (shared with resolve/build scripts):

```json
{"refId": "C1", "title": "...", "authors": [{"family": "Smith", "given": "J"}],
 "year": "2020", "journal": "...", "volume": "1", "issue": "2", "pages": "3-4",
 "doi": "10.x/y", "pmid": "123", "abstract": "...", "url": "...",
 "type": "article-journal", "sources": ["openalex", "pubmed"]}
```

Records from several sources are merged by DOI/PMID.

## Good practice

- Query by concept, not by the whole sentence: 3–7 content words, English terms for international databases.
- Use `--from-year` for fast-moving topics; keep older landmark papers when the claim is historical.
- Read the abstract before choosing. A paper supports a claim only if its findings actually state it.
- Prefer primary studies for specific findings and reviews for broad statements; avoid retracted papers.
- `lookup --doi/--pmid` returns canonical metadata; use it for any DOI suggested from memory — if lookup fails, the reference is not used.
- Politeness: set `ZWLC_MAILTO=<email>` for Crossref/OpenAlex; `NCBI_API_KEY` raises PubMed limits. Without a key, keep PubMed to ~3 requests/second (the script makes 2 per search).
- Network failures of one source are warnings; the other sources still return.

Host tools (PubMed MCP, web search, Consensus...) may be used to discover papers, but the final list must come back through `lookup` so metadata is real and consistent.
