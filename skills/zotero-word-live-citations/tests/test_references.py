"""Normalization, literature-search parsing, Zotero matching and RIS building."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES

import build_import_file
import resolve_references as rr
import search_literature as sl
from _common import item_uri, normalize_doi, normalize_title, title_similarity


def zitem(key, title, doi=None, year="2020", author="Smith", item_type="journalArticle",
          parent=None, extra="", lib_id=111):
    data = {"key": key, "itemType": item_type, "title": title, "DOI": doi or "", "date": year,
            "creators": [{"lastName": author, "firstName": "A"}], "extra": extra}
    if parent:
        data["parentItem"] = parent
    return {"key": key, "library": {"type": "user", "id": lib_id}, "data": data}


class FakeLibrary:
    def __init__(self, items):
        self.items = items

    def search(self, q, everything):
        ql = q.lower()
        hits = []
        for it in self.items:
            d = it["data"]
            hay = (d["title"] + " " + d["creators"][0]["lastName"]).lower()
            if everything:
                hay += " " + (d["DOI"] or "").lower() + " " + d["extra"].lower()
            if ql in hay or all(w in normalize_title(hay) for w in normalize_title(q).split()):
                hits.append(it)
        return hits

    def fetch(self, key):
        return next(it for it in self.items if it["key"] == key)

    def resolve(self, ref):
        return rr.resolve_one(ref, self.search, self.fetch)


class NormalizationTests(unittest.TestCase):
    def test_doi(self):
        for raw in ("https://doi.org/10.1038/NATURE13980.", "doi: 10.1038/nature13980",
                    "http://dx.doi.org/10.1038/nature13980)", "10.1038%2Fnature13980"):
            self.assertEqual(normalize_doi(raw), "10.1038/nature13980", raw)
        self.assertIsNone(normalize_doi("not a doi"))

    def test_title(self):
        self.assertEqual(normalize_title("The <i>Roles</i> of Café—Receptors!"), "the roles of cafe receptors")
        self.assertEqual(title_similarity("PD-1 blockade in melanoma", "PD 1 Blockade in Melanoma."), 1.0)
        self.assertLess(title_similarity("PD-1 blockade in melanoma", "CAR T cells in leukemia"), 0.5)

    def test_item_uri_uses_items_own_library(self):
        self.assertEqual(item_uri(zitem("ABCD1234", "t")), "http://zotero.org/users/111/items/ABCD1234")
        group = {"key": "ABCD1234", "library": {"type": "group", "id": 42}}
        self.assertEqual(item_uri(group), "http://zotero.org/groups/42/items/ABCD1234")
        with self.assertRaises(ValueError):
            item_uri({"key": "ABCD1234", "library": {"type": "user", "id": 0}})


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.lib = FakeLibrary([
            zitem("DOI00001", "Checkpoint blockade in melanoma", doi="10.1000/abc"),
            zitem("TITLE001", "Checkpoint blockade in melanoma revisited", year="2021", author="Jones"),
            zitem("ATTACH01", "Checkpoint blockade in melanoma", item_type="attachment", parent="DOI00001"),
            zitem("PMID0001", "Tumour antigens", extra="PMID: 123456"),
            zitem("DUP00001", "Same DOI twice", doi="10.9999/dup"),
            zitem("DUP00002", "Same DOI twice", doi="10.9999/dup"),
            zitem("AMB00001", "Neoantigen vaccines for cancer", year="2019", author="Lee"),
            zitem("AMB00002", "Neoantigen vaccines for cancers", year="2019", author="Lee"),
        ])

    def test_doi_beats_fuzzy_title(self):
        status, payload = self.lib.resolve({"title": "Checkpoint blockade in melanoma revisited",
                                            "doi": "10.1000/abc", "year": "2021"})
        self.assertEqual((status, payload["item"]["key"], payload["matchMethod"]), ("resolved", "DOI00001", "doi"))

    def test_pmid_match(self):
        status, payload = self.lib.resolve({"title": "x", "pmid": "123456"})
        self.assertEqual((status, payload["item"]["key"]), ("resolved", "PMID0001"))

    def test_attachment_never_matched(self):
        status, payload = self.lib.resolve({"title": "Checkpoint blockade in melanoma", "year": "2020"})
        self.assertEqual(status, "resolved")
        self.assertEqual(payload["item"]["key"], "DOI00001")

    def test_shared_doi_is_ambiguous_and_duplicate(self):
        status, payload = self.lib.resolve({"title": "Same DOI twice", "doi": "10.9999/dup"})
        self.assertEqual(status, "ambiguous")
        self.assertEqual(payload["duplicateKeys"], ["DUP00001", "DUP00002"])

    def test_close_candidates_are_ambiguous_not_silently_chosen(self):
        status, payload = self.lib.resolve({"title": "Neoantigen vaccine for cancer", "year": "2019",
                                            "authors": [{"family": "Lee"}]})
        self.assertEqual(status, "ambiguous")
        self.assertEqual({c["key"] for c in payload["candidates"]}, {"AMB00001", "AMB00002"})

    def test_year_conflict_blocks_fuzzy_match(self):
        status, _ = self.lib.resolve({"title": "Checkpoint blockade in melanoma revisited", "year": "1999",
                                      "authors": [{"family": "Other"}]})
        self.assertEqual(status, "missing")

    def test_manual_pin_rejects_attachment(self):
        self.assertEqual(self.lib.resolve({"zoteroKey": "ATTACH01"})[0], "missing")
        self.assertEqual(self.lib.resolve({"zoteroKey": "TITLE001"})[1]["matchMethod"], "manual")

    def test_parse_text_and_ris(self):
        refs = rr.parse_text("1. Smith A, Lee B. Checkpoint blockade in melanoma. N Engl J Med. 2020;1:2. "
                             "doi:10.1000/ABC.\n[2] Jones C. (2021). Another title. Journal.\n")
        self.assertEqual([r["refId"] for r in refs], ["1", "2"])
        self.assertEqual(refs[0]["title"], "Checkpoint blockade in melanoma")
        self.assertEqual(refs[0]["doi"], "10.1000/abc")
        self.assertEqual(refs[1]["title"], "Another title")
        ris = rr.parse_ris("TY  - JOUR\nTI  - A title\nAU  - Smith, Anna\nPY  - 2020\nDO  - 10.1000/x\n"
                           "SP  - 5\nEP  - 9\nAN  - PMID:777777\nER  - \n")
        self.assertEqual(ris[0]["title"], "A title")
        self.assertEqual(ris[0]["pages"], "5-9")
        self.assertEqual(ris[0]["pmid"], "777777")


class SearchParserTests(unittest.TestCase):
    def setUp(self):
        self.api = json.loads((FIXTURES / "api_responses.json").read_text(encoding="utf-8"))

    def test_parsers_and_merge(self):
        cr = sl.parse_crossref(self.api["crossref"])
        oa = sl.parse_openalex(self.api["openalex"])
        pm = sl.parse_pubmed_xml((FIXTURES / "pubmed_efetch.xml").read_text(encoding="utf-8"))
        self.assertEqual(cr[0]["doi"], "10.1016/s0959-4388(00)00234-8")
        self.assertEqual(cr[0]["abstract"], "Combined psychophysical and neurophysiological research.")
        self.assertEqual(oa[0]["pages"], "1756-1762")
        self.assertEqual(oa[0]["pmid"], "26551544")
        self.assertEqual(oa[0]["abstract"], "Piezo2 senses limb position")
        self.assertEqual(pm[0]["title"], "The roles and functions of cutaneous mechanoreceptors")
        self.assertEqual(pm[0]["doi"], "10.1016/s0959-4388(00)00234-8")
        merged = sl.merge_records(cr + oa + pm)
        self.assertEqual(len(merged), 2)
        johnson = next(r for r in merged if r["pmid"] == "11502392")
        self.assertEqual(johnson["sources"], ["crossref", "openalex", "pubmed"])
        self.assertEqual([r["refId"] for r in merged], ["C1", "C2"])


class BuildImportTests(unittest.TestCase):
    def test_only_missing_titled_records_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data = {"resolved": {"A": {"key": "KEY00001"}},
                    "missing": [{"refId": "B"}, {"refId": "C"}],
                    "references": [
                        {"refId": "A", "title": "In library"},
                        {"refId": "B", "title": "Missing & new", "authors": [{"family": "Wu", "given": "Li"}],
                         "year": "2022", "journal": "J", "pages": "10–12", "doi": "10.5555/b", "pmid": "4242424"},
                        {"refId": "C", "raw": "unparsable citation"}]}
            (tmp / "map.json").write_text(json.dumps(data), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code = build_import_file.main(["--map", str(tmp / "map.json"), "--out", str(tmp / "m.ris"),
                                               "--tag", "zwlc-import"])
            self.assertEqual(code, 1)  # C skipped -> reported
            self.assertIn("C: no structured title", err.getvalue())
            ris = (tmp / "m.ris").read_text(encoding="utf-8")
            self.assertEqual(ris.count("TY  - "), 1)
            for line in ("TI  - Missing & new", "AU  - Wu, Li", "SP  - 10", "EP  - 12", "DO  - 10.5555/b",
                         "AN  - PMID:4242424", "KW  - zwlc-import", "ER  - "):
                self.assertIn(line, ris)
            back = rr.parse_ris(ris)
            self.assertEqual((back[0]["doi"], back[0]["pmid"], back[0]["year"]), ("10.5555/b", "4242424", "2022"))


class LoginStateTests(unittest.TestCase):
    def _state(self, status, body):
        from _common import Response, ZoteroLocal

        z = ZoteroLocal()
        z.request = lambda *a, **k: Response(status=status, headers={}, text=body)
        return z.login_state()

    def test_signed_in(self):
        body = json.dumps([{"key": "ABCD1234", "library": {"type": "user", "id": 42}}])
        self.assertEqual(self._state(200, body), (True, 42))

    def test_not_signed_in(self):
        body = json.dumps([{"key": "ABCD1234", "library": {"type": "user", "id": 0}}])
        self.assertEqual(self._state(200, body), (False, None))

    def test_empty_library_or_api_down_is_unknown(self):
        self.assertEqual(self._state(200, "[]"), (None, None))
        self.assertEqual(self._state(None, ""), (None, None))


class DeploymentBugTests(unittest.TestCase):
    def test_bad_doi_placeholder_does_not_match_item_without_doi(self):
        import insert_zotero_fields as ins
        from _common import UsageError

        pool = ins.ItemPool({"resolved": {"R1": {"key": "AAAA1111", "uri": "u", "itemData": {}}}}, "http://x")
        with self.assertRaises(UsageError):
            pool.get("doi", "not-a-doi")

    def test_author_date_label_without_year(self):
        import insert_zotero_fields as ins

        self.assertEqual(ins.author_year_label({"author": [{"family": "Smith"}]}), "Smith, n.d.")

    def test_unknown_pinned_key_is_missing_not_fatal(self):
        from _common import ZoteroHTTPError

        def fetch(key):
            raise ZoteroHTTPError(f"GET {key} failed: status=404", 404)

        status, payload = rr.resolve_one({"refId": "A", "zoteroKey": "ZZZZ9999"}, lambda q, e: [], fetch)
        self.assertEqual(status, "missing")
        self.assertTrue(payload["pinnedKey"])

    def test_unreachable_zotero_still_aborts_pinned_lookup(self):
        def fetch(key):
            raise ConnectionError("status=None connection refused")

        with self.assertRaises(ConnectionError):
            rr.resolve_one({"refId": "A", "zoteroKey": "ZZZZ9999"}, lambda q, e: [], fetch)

    def test_in_library_missing_items_are_not_exported_for_import(self):
        data = {"references": [{"refId": "A", "title": "Already there"}, {"refId": "B", "title": "New"}],
                "resolved": {},
                "missing": [{"refId": "A", "inLibrary": True, "reason": "cannot verify library namespace"},
                            {"refId": "B", "reason": "no library item matched the title"}]}
        with tempfile.TemporaryDirectory() as tmp:
            map_path, out = Path(tmp) / "map.json", Path(tmp) / "missing.ris"
            map_path.write_text(json.dumps(data), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                build_import_file.main(["--map", str(map_path), "--out", str(out)])
            ris = out.read_text(encoding="utf-8")
        self.assertIn("TI  - New", ris)
        self.assertNotIn("Already there", ris)

    def test_explicit_ref_id_cannot_export_ambiguous_or_resolved(self):
        data = {"references": [{"refId": r, "title": f"T{r}"} for r in "ABCD"],
                "resolved": {"A": {"key": "KEY00001"}},
                "missing": [{"refId": "D", "reason": "no match"}],
                "ambiguous": [{"refId": "B", "reason": "2 library items share this DOI"}]}
        with tempfile.TemporaryDirectory() as tmp:
            map_path, out = Path(tmp) / "map.json", Path(tmp) / "missing.ris"
            map_path.write_text(json.dumps(data), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code = build_import_file.main(["--map", str(map_path), "--out", str(out),
                                               "--ref-id", "A", "--ref-id", "B", "--ref-id", "C"])
            self.assertEqual(code, 1)
            self.assertFalse(out.exists())
            self.assertIn("B: ambiguous", err.getvalue())
            self.assertIn("C: not listed as missing", err.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                code = build_import_file.main(["--map", str(map_path), "--out", str(out), "--ref-id", "D"])
            self.assertEqual(code, 0)
            self.assertIn("TI  - TD", out.read_text(encoding="utf-8"))

    def test_import_checks_library_and_collection_ids(self):
        from unittest import mock

        import zotero_local
        from _common import Response

        target = {"libraryID": 2, "libraryName": "Group B", "id": 7, "name": "Inbox", "editable": True}
        calls = []

        def fake_request(self, path, method="GET", data=None, **kw):
            calls.append(path)
            if "getSelectedCollection" in path:
                return Response(status=200, headers={}, text=json.dumps(target))
            return Response(status=201, headers={}, text="[]")

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(zotero_local.ZoteroLocal, "request", fake_request):
            ris = Path(tmp) / "m.ris"
            ris.write_text("TY  - JOUR\nTI  - X\nER  - \n", encoding="utf-8")
            base = ["import-ris", "--file", str(ris), "--expect-target", "Inbox", "--yes"]
            with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()):
                code = zotero_local.main(base + ["--expect-library-id", "1", "--expect-collection-id", "7"])
            self.assertEqual(code, 2)
            self.assertIn("libraryID=2", err.getvalue())
            self.assertFalse(any("/connector/import" in c for c in calls))
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                code = zotero_local.main(base + ["--expect-library-id", "2", "--expect-collection-id", "7"])
            self.assertEqual(code, 0)
            self.assertTrue(any("/connector/import" in c for c in calls))

    def test_local_requests_bypass_proxy(self):
        import http.server
        import os
        import threading
        from unittest import mock

        import _common

        class Ok(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Ok)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        env = {k: v for k, v in os.environ.items() if k.lower() != "no_proxy"}
        env.update(HTTP_PROXY="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9")
        try:
            with mock.patch.dict(os.environ, env, clear=True):
                response = _common.http(f"http://127.0.0.1:{server.server_port}/", timeout=5)
        finally:
            server.shutdown()
            server.server_close()
        self.assertTrue(response.ok, response.error)


    def test_duplicate_ref_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refs.json"
            path.write_text(json.dumps([{"refId": "C1", "title": "A"}, {"refId": "C1", "title": "B"}]),
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate refId 'C1'"):
                rr.load_references(path)

    def test_lookup_keeps_good_records_when_one_doi_fails(self):
        from unittest import mock

        def fake_get(url, timeout):
            if "10.9999" in url:
                raise ConnectionError("status=404")
            return mock.Mock(json=lambda: {"message": {"DOI": "10.1000/ok", "title": ["Real"]}})

        with mock.patch.object(sl, "_get", fake_get), mock.patch.object(sl, "pubmed_fetch", lambda ids, t: []):
            records, failures = sl.lookup(["10.1000/ok", "10.9999/nope", "junk"], ["123"], None, 5)
        self.assertEqual([r["doi"] for r in records], ["10.1000/ok"])
        self.assertEqual(len(failures), 3)

if __name__ == "__main__":
    unittest.main()
