# Zotero fields in DOCX (OOXML)

## Citation field

Instruction text: ` ADDIN ZOTERO_ITEM CSL_CITATION <JSON> ` inside a Word complex field:

```xml
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM CSL_CITATION {...} </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:t xml:space="preserve">[1]</w:t></w:r>          <!-- provisional visible result -->
<w:r><w:fldChar w:fldCharType="end"/></w:r>
```

JSON written by `insert_zotero_fields.py`:

```json
{"citationID": "aB3dE9xZ",
 "properties": {"noteIndex": 0},
 "citationItems": [{"id": "ABCD1234",
                    "uris": ["http://zotero.org/users/123456/items/ABCD1234"],
                    "itemData": {"id": "http://zotero.org/users/123456/items/ABCD1234",
                                 "type": "article-journal", "title": "..."}}],
 "schema": "https://github.com/citation-style-language/schema/raw/master/csl-citation.json"}
```

- One field per location, unique `citationID` per field (8 random alphanumerics, checked against existing ones). Same item cited twice → two fields, two IDs. Several items at one place → one field, several `citationItems`.
- `noteIndex` 0 for body text. Footnote/endnote citations are not inserted by this version.
- `itemData` is Zotero's own CSL-JSON (`?format=csljson`), so the citation survives in documents opened by people without the item.
- `formattedCitation` / `plainCitation` are not written; Zotero Refresh creates them.
- Field runs copy the `w:rPr` of the text they follow. JSON is XML-escaped (`& < >`).
- Accepted URI namespaces: `users/<id>`, `users/local/<key>`, `groups/<id>`. `citationItems[].id` (when it is an 8-char key) must equal the URI's key.

## Bibliography field

```text
 ADDIN ZOTERO_BIBL {"uncited":[],"omitted":[],"custom":[]} CSL_BIBLIOGRAPHY 
```

Written after the heading paragraph given by `--bibliography-heading` (created at the end if absent). The field result spans one paragraph per provisional entry: `begin/instr/separate` in the first paragraph, `end` in the last. Refresh replaces the entries. An existing `ZOTERO_BIBL` is kept and not duplicated.

## Document preferences

Stored as custom document properties `ZOTERO_PREF_1..n` in `docProps/custom.xml` (value chunks ≤ 255 chars, concatenated in order). This format was verified end to end with Zotero 10.0.2 + Word 16 (Microsoft 365): Zotero → Refresh accepted the prefs and reformatted all citations and the bibliography (re-check after Zotero upgrades):

```xml
<data data-version="3" zotero-version="10.0.2"><session id="Ab12Cd34"/>
<style id="http://www.zotero.org/styles/vancouver" locale="en-US" hasBibliography="1" bibliographyStyleHasBeenSet="1"/>
<prefs><pref name="fieldType" value="Field"/><pref name="automaticJournalAbbreviations" value="true"/><pref name="noteType" value="0"/></prefs></data>
```

If the document already has `ZOTERO_PREF_*`, it is left untouched (its style wins). A missing `custom.xml` is created together with its `_rels/.rels` relationship and `[Content_Types].xml` override. Word on some platforms stores the same data as `w:docVar` in `word/settings.xml`; the validator reads both.

Style aliases: `vancouver`, `apa`, `nature`, `ieee`, `ama`, `chicago-author-date`, `harvard`, `gb-t-7714-numeric`, `gb-t-7714-author-date`; any `http://www.zotero.org/styles/<id>` URL works if that style is installed in Zotero. Author–date styles get `(Author, Year)` provisional text and a leading space; numeric styles get `[n]` numbered by first appearance.

## What is (not) touched

Only `word/document.xml`, `docProps/custom.xml`, `[Content_Types].xml`, `_rels/.rels` change, via targeted string edits; all other parts are copied byte-for-byte with their original ZIP metadata. Text inside existing fields and `w:fldSimple` is never split. Paragraphs that contain text boxes are skipped (their inner paragraphs are editable).
