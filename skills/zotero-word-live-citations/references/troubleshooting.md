# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `selftest`: zotero-running NO | Start Zotero Desktop. Firewalls/VPN tools sometimes block 127.0.0.1:23119. |
| connector OK but `/api/` fails | Zotero ≥ 7 needed; tick *Allow other applications on this computer to communicate with Zotero* (Settings → Advanced). |
| `Python was not found` on Windows | That is the Microsoft Store stub. Install Python 3.9+ or use `py -3` / the Codex bundled Python. |
| `cannot verify library namespace` | The library is local-only (never synced). Sync to zotero.org once, or cite from a group library. |
| DOI known to be in Zotero but `missing` | DOI stored only in *Extra*/URL with a different form, or the item is in a group library (`--library group:<id>`). Pin with `"zoteroKey"`. |
| Newly imported items still `missing` | Zotero was still indexing; wait a few seconds and resolve again. Check the target collection was editable. |
| `anchor matches N places` | Add `occurrence`, `paragraph` or `paragraphContains`. |
| `anchor not found` | Text differs (hyphen, non-breaking space, tracked changes). Check `--list-paragraphs`; anchors cannot span existing fields. |
| Word shows `{ ADDIN ZOTERO_ITEM ...}` code | Field codes view is on: Alt+F9. |
| Refresh: "citation has been modified" | Someone edited the visible text of a field. Choose *No* to keep Zotero's version, or Undo. Do not click through many of these; report. |
| Refresh: "item not found in your library" | Citation from another library; embedded `itemData` keeps it working. Do not relink unless asked. |
| Style not applied after Refresh | Style id not installed in Zotero: Zotero → Settings → Cite → install it, then Document Preferences in Word. |
| Word add-in missing | Zotero → Settings → Cite → Word Processors → Reinstall Microsoft Word Add-in; restart Word. |
| Document damaged after another editor | WPS/Pages/LibreOffice can convert fields to text. Go back to the last good copy. |
