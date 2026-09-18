import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from helpers import make_docx, read_part, ref_map, run, zotero_field

import insert_zotero_fields as ins
import validate_zotero_docx as val
from _common import sha256_file

CUSTOM = ('<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/'
          'officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/'
          '2006/docPropsVTypes"><property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" '
          'name="Client"><vt:lpwstr>ACME</vt:lpwstr></property></Properties>')


class InsertTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_dir.name) / "路径 with space"
        self.tmp.mkdir()
        self.map = ref_map(self.tmp)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def insert(self, src, *extra, expect=0):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()) as err:
            code = ins.main(["--input", str(src), "--items", str(self.map), "--zotero-version", "test",
                             *map(str, extra)])
        self.assertEqual(code, expect, err.getvalue())
        return json.loads(out.getvalue()) if code in (0, 1) else err.getvalue()

    def placements(self, spec):
        path = self.tmp / "placements.json"
        path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        return path

    def fields(self, docx):
        return val.inspect_docx(docx)

    def test_single_and_combined_citation_across_split_runs(self):
        src = make_docx(self.tmp / "in.docx", [
            run("Hair cells transduce ") + run("sound", bold=True) + run(" mechanically. Channels open fast."),
            run("References")])
        pl = self.placements({"placements": [
            {"anchor": "transduce sound mechanically", "refs": ["R1"]},
            {"anchor": "Channels open fast", "refs": ["R2", "R3"]}]})
        report = self.insert(src, "--placements", pl, "--bibliography-heading", "References")
        self.assertEqual(report["structuralValidation"], "passed", report["validationErrors"])
        self.assertEqual(report["fieldsInserted"], 2)
        self.assertEqual(report["citationItemOccurrences"], 3)
        self.assertEqual(report["embeddedItemData"], "3/3")
        self.assertTrue(report["inputUnchanged"])
        out = Path(report["outputDocument"])
        self.assertEqual(out.name, "in-zotero-cited.docx")
        result = self.fields(out)
        combined = [f for f in result["zoteroFields"] if f["itemCount"] == 2]
        self.assertEqual(len(combined), 1, "two items at one place must share one field")
        self.assertEqual(len({f["citationID"] for f in result["zoteroFields"]}), 2)
        self.assertEqual(len(result["bibliographyFields"]), 1)
        self.assertEqual(result["documentPreferences"]["styleID"], "http://www.zotero.org/styles/vancouver")
        doc = read_part(out, "word/document.xml")
        # anchor text itself unchanged and bold run formatting copied into field runs
        text = "".join(ins.segments(doc, 0)[i].text for i in range(len(ins.segments(doc, 0))))
        self.assertIn("Hair cells transduce sound mechanically.", text)
        self.assertEqual(read_part(out, "word/unknownExtension.xml"), '<x:ext xmlns:x="urn:vendor">keep me</x:ext>')
        self.assertIn("xmlns:w14=", doc)

    def test_same_item_twice_gets_two_citation_ids(self):
        src = make_docx(self.tmp / "in.docx", [run("Alpha claim. Beta claim.")])
        pl = self.placements({"placements": [{"anchor": "Alpha claim", "refs": ["R1"]},
                                             {"anchor": "Beta claim", "refs": ["R1"]}]})
        report = self.insert(src, "--placements", pl)
        ids = [p["citationID"] for p in report["placements"]]
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(report["uniqueItems"], 1)
        self.assertEqual([p["visibleText"] for p in report["placements"]], ["[1]", "[1]"])

    def test_placeholders_split_across_runs_are_replaced(self):
        src = make_docx(self.tmp / "in.docx", [
            run("Claim one [@ref:") + run("R1; @ref:R2]") + run(". Claim two [@zotero:CCCC3333].")])
        report = self.insert(src, "--placeholders")
        self.assertEqual(report["fieldsInserted"], 2)
        doc = read_part(Path(report["outputDocument"]), "word/document.xml")
        self.assertNotIn("[@", "".join(s.text for s in ins.segments(doc, 0)))
        self.assertEqual(report["placements"][0]["visibleText"], "[1,2]")

    def test_existing_citations_preserved_and_custom_props_extended(self):
        src = make_docx(self.tmp / "in.docx", [run("Old claim") + zotero_field("oldCite1", "ZZZZ9999") +
                                               run(". New claim here.")], custom_xml=CUSTOM)
        pl = self.placements({"placements": [{"anchor": "New claim here", "refs": ["R1"]}]})
        report = self.insert(src, "--placements", pl, "--no-bibliography")
        self.assertEqual(report["structuralValidation"], "passed", report["validationErrors"])
        out = Path(report["outputDocument"])
        result = self.fields(out)
        self.assertIn("oldCite1", [f["citationID"] for f in result["zoteroFields"]])
        custom = read_part(out, "docProps/custom.xml")
        self.assertIn('name="Client"', custom)
        self.assertIn('name="ZOTERO_PREF_1"', custom)
        self.assertEqual(report["placements"][0]["visibleText"], "[2]")

    def test_existing_prefs_are_kept(self):
        prefs_custom = CUSTOM.replace('name="Client"><vt:lpwstr>ACME', 'name="ZOTERO_PREF_1"><vt:lpwstr>'
                                      '&lt;data data-version="3"&gt;&lt;style id="http://www.zotero.org/styles/apa"/&gt;&lt;/data&gt;')
        src = make_docx(self.tmp / "in.docx", [run("A claim.")], custom_xml=prefs_custom)
        pl = self.placements({"placements": [{"anchor": "A claim", "refs": ["R1"]}]})
        report = self.insert(src, "--placements", pl, "--style", "vancouver")
        self.assertEqual(report["documentPreferences"], "kept-existing")
        self.assertEqual(self.fields(Path(report["outputDocument"]))["documentPreferences"]["styleID"],
                         "http://www.zotero.org/styles/apa")

    def test_ambiguous_anchor_and_same_location_rejected(self):
        src = make_docx(self.tmp / "in.docx", [run("Repeat. Repeat.")])
        err = self.insert(src, "--placements",
                          self.placements({"placements": [{"anchor": "Repeat", "refs": ["R1"]}]}), expect=2)
        self.assertIn("matches 2 places", err)
        err = self.insert(src, "--placements", self.placements({"placements": [
            {"anchor": "Repeat", "occurrence": 1, "refs": ["R1"]},
            {"anchor": "Repeat", "occurrence": 1, "refs": ["R2"]}]}), expect=2)
        self.assertIn("same location", err)

    def test_unresolved_ref_aborts_without_output(self):
        src = make_docx(self.tmp / "in.docx", [run("Claim [@ref:NOPE].")])
        err = self.insert(src, "--placeholders", expect=2)
        self.assertIn("not resolved", err)
        self.assertFalse((self.tmp / "in-zotero-cited.docx").exists())

    def test_refuses_to_overwrite_input_or_existing_output(self):
        src = make_docx(self.tmp / "in.docx", [run("Claim [@ref:R1].")])
        before = sha256_file(src)
        err = self.insert(src, "--placeholders", "--output", src, expect=2)
        self.assertIn("must differ", err)
        self.insert(src, "--placeholders")
        err = self.insert(src, "--placeholders", expect=2)
        self.assertIn("output exists", err)
        self.assertEqual(sha256_file(src), before)

    def test_report_path_cannot_overwrite_input_or_output(self):
        src = make_docx(self.tmp / "in.docx", [run("Claim [@ref:R1].")])
        before = sha256_file(src)
        err = self.insert(src, "--placeholders", "--report", src, expect=2)
        self.assertIn("--report must differ", err)
        out = self.tmp / "cited.docx"
        err = self.insert(src, "--placeholders", "--output", out, "--report", out, expect=2)
        self.assertIn("--report must differ", err)
        self.assertEqual(sha256_file(src), before)
        self.assertFalse(out.exists())

    def test_prefixed_custom_properties_are_extended(self):
        ns = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
        prefixed = (CUSTOM.replace(f'<Properties xmlns="{ns}"', f'<cp:Properties xmlns:cp="{ns}"')
                    .replace("<property ", "<cp:property ").replace("</property>", "</cp:property>")
                    .replace("</Properties>", "</cp:Properties>"))
        src = make_docx(self.tmp / "in.docx", [run("A claim.")], custom_xml=prefixed)
        pl = self.placements({"placements": [{"anchor": "A claim", "refs": ["R1"]}]})
        report = self.insert(src, "--placements", pl, "--no-bibliography")
        self.assertEqual(report["documentPreferences"], "added")
        custom = read_part(Path(report["outputDocument"]), "docProps/custom.xml")
        self.assertIn('<cp:property fmtid=', custom)
        self.assertIn('name="ZOTERO_PREF_1"', custom)
        self.assertIsNotNone(self.fields(Path(report["outputDocument"]))["documentPreferences"])

    def test_author_date_style_visible_text(self):
        src = make_docx(self.tmp / "in.docx", [run("Claim.")])
        pl = self.placements({"placements": [{"anchor": "Claim", "refs": ["R1", "R2"]}]})
        report = self.insert(src, "--placements", pl, "--style", "apa")
        self.assertEqual(report["placements"][0]["visibleText"], "(Smith, 2020; Smith, 2019)")


    def test_existing_citation_with_split_instruction_is_numbered(self):
        # Word often splits one field instruction over several instrText runs
        field = zotero_field("oldCite1", "ZZZZ9999")
        head, sep, tail = field.partition('CSL_CITATION ')
        split = head + sep + '</w:instrText></w:r><w:r><w:instrText xml:space="preserve">' + tail
        ids, fields, has_bibl = ins.existing_citations(split)
        self.assertEqual(ids, {"oldCite1"})
        self.assertEqual(fields[0][1], ["http://zotero.org/users/111/items/ZZZZ9999"])
        self.assertFalse(has_bibl)
        src = make_docx(self.tmp / "in.docx", [run("Old claim") + split + run(". New claim here.")])
        pl = self.placements({"placements": [{"anchor": "New claim here", "refs": ["R1"]}]})
        report = self.insert(src, "--placements", pl, "--no-bibliography")
        self.assertEqual(report["placements"][0]["visibleText"], "[2]")

    def test_author_date_detection_uses_style_name(self):
        self.assertTrue(ins.AUTHOR_DATE_RE.search("apa"))
        self.assertTrue(ins.AUTHOR_DATE_RE.search("apa-6th-edition"))
        self.assertTrue(ins.AUTHOR_DATE_RE.search("elsevier-harvard"))
        self.assertFalse(ins.AUTHOR_DATE_RE.search("japanese-journal-of-applied-physics"))
        self.assertFalse(ins.AUTHOR_DATE_RE.search("vancouver"))

    def test_deep_markdown_headings_become_heading3(self):
        import md_to_docx
        body = md_to_docx.convert("# T\n\n#### Deep\n")
        self.assertIn('<w:pStyle w:val="Heading3"/>', body)
        self.assertNotIn("####", body)

if __name__ == "__main__":
    unittest.main()
