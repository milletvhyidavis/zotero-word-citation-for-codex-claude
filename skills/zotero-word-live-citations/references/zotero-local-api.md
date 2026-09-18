# Zotero Desktop local API and connector (as used by the scripts)

Base URL `http://127.0.0.1:23119` (override with `--base-url` or `ZOTERO_LOCAL_BASE_URL`).
Requirement: Zotero 7+ running, Settings → Advanced → *Allow other applications on this computer to communicate with Zotero* (this also enables `/api/`). Verified against Zotero 10.0.2.

## Read routes (no API key)

| Purpose | Route |
|---|---|
| status | `GET /api/`, `GET /connector/ping` (header `X-Zotero-Version`) |
| probe items | `GET /api/users/0/items/top?limit=1&format=keys` |
| title/creator/year search | `GET /api/users/0/items/top?q=<text>&format=json` |
| DOI / PMID / any field search | `GET /api/users/0/items/top?q=<doi>&qmode=everything` |
| one item | `GET /api/users/0/items/<KEY>` |
| CSL-JSON itemData | `GET /api/users/0/items/<KEY>?format=csljson` → `[{"id": "http://zotero.org/users/<id>/items/<KEY>", ...}]` |
| collections | `GET /api/users/0/collections?limit=100&start=N` |
| groups | `GET /api/users/0/groups`; group items under `/api/groups/<id>/...` |

`users/0` means "the local user"; the real library identity comes from each item's `library` object (`{"type": "user", "id": 123456}`) — the URI is built from that object only. If `id` is not a positive number (unsynced local library), `item_uri()` refuses; use a URI from an existing Zotero-generated field or sync the library.

`/items/top` excludes child attachments/notes; the scripts additionally drop `attachment`, `note`, `annotation` types and anything with `parentItem`.

## Write route (approval required)

| Purpose | Route |
|---|---|
| current target | `POST /connector/getSelectedCollection` `{}` → `{libraryName, name, id, editable, targets[...]}` |
| import RIS/BibTeX | `POST /connector/import?session=<uuid>` body = file text, `Content-Type: text/plain` |

The connector imports into the library/collection **selected in the Zotero window**; there is no collection parameter. `import-*` therefore prints the target, refuses without `--yes`, and with `--expect-target NAME` refuses when the selection differs. The local API itself is read-only.

Header `Zotero-API-Version: 3` is sent on `/api`, `X-Zotero-Connector-API-Version: 3` on `/connector`.
