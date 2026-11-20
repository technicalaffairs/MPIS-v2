# MPIS v2 — نظام معلومات إجراءات الصيانة (النسخة الحديثة)

# MPIS v2 — Maintenance Procedure Information System (modern rebuild)

> **نفس المعلومات بالظبط — بدون أي تعديل أو إضافة أو حذف.**
> **Same information, exactly — nothing added, changed, or deleted.**

This repository is a modern rebuild of the original MPIS repository
(`technicalaffairs/MPIS`): ~17,000 old FrontPage files and 136 PDFs,
rebuilt as structured data + a modern static website.

- **No PDF files.** Every PDF was converted to text (see `content/`).
- **Multilingual by design.** Every document is one JSON file with
  `title_ar` / `title_en` and a `translation_status`. The site flips
  between Arabic (RTL) and English (LTR) on every page. Adding a third
  language means adding one file in `i18n/` and one field per document —
  no redesign.
- **No secrets in code.** The old `chat_server.py` contained a hard-coded
  Cohere API key. It is **not** in this repository. `server.py` reads
  `COHERE_API_KEY` from the environment only (see `.env.example`).

---

## الأرقام / Numbers

| | |
|---|---|
| Source files in v1 (GitHub tree) | 17,615 entries / 16,928 files |
| HTML pages migrated | 4,456 of 4,468 (3 had no text and no title — listed in the report) |
| PDFs converted to text | 68 unique of 136 files (68 were byte-identical duplicates, mostly in `new/`) |
| JSON documents in `content/` | **4,525** |
| Documents with both languages | 2,424 |
| Documents still missing a translation | 2,095 — shown as-is, flagged, never faked |
| Partially bilingual documents | 6 |
| Categories | 28 |
| Images copied from v1 (referenced diagrams) | 2,925 |

## البنية / Structure

```
mpis-v2/
├── README.md               this file
├── MIGRATION_REPORT.md     exact counts, what migrated, what did not
├── migration_log.json      machine-readable migration log
├── .env.example            environment variables (copy to .env; never commit .env)
├── .gitignore
├── server.py               stdlib-only server: serves site/dist + /api/search
├── content/                one JSON file per document + index.json
│   ├── index.json          manifest: id, doc_number, titles, category, language, status
│   └── <id>.json           id, doc_number, title_ar, title_en, category,
│                           source_path, language, languages_available,
│                           translation_status, sections, text, links, images
├── i18n/
│   ├── ar.json             UI strings (Arabic)
│   └── en.json             UI strings (English) — a third language is a new file here
├── site/
│   ├── dist/               generated site (regenerate with tools/build_site.py)
│   └── src/                (reserved for future hand-written templates)
└── tools/
    ├── migrate.py          HTML + PDF -> JSON converter (stdlib only, repeatable)
    ├── build_site.py       JSON -> static site generator (stdlib only)
    └── translate_t024_ter.py  the one new Arabic translation created for v2
```

## التشغيل / How to run

```bash
# 1. Re-run the migration (source = a checkout of the v1 repo)
python3 tools/migrate.py --source /path/to/MPIS-v1 --out content --log migration_log.json
python3 tools/translate_t024_ter.py        # adds the T-024-ter Arabic version

# 2. Build the site
python3 tools/build_site.py --content content --dist site/dist

# 3. Serve it (stdlib only — no install needed)
python3 server.py --port 8000
# open http://localhost:8000/
# search API: http://localhost:8000/api/search?q=transformer
```

Or open `site/dist/index.html` directly in a browser (search needs the
HTTP server, because `fetch` does not load `search.json` from `file://`
in some browsers).

## إضافة لغة جديدة / Adding a language

1. Add `i18n/<lang>.json` with the same keys as `i18n/en.json`.
2. Add a `title_<lang>` field to the documents you translate and set
   `translation_status` to `available` for those documents.
3. Add the language to the switcher in `tools/build_site.py`
   (search for `langBtn`) and rebuild. No other change is needed.

## الترجمة / Translation policy

- Text was extracted **verbatim** (whitespace normalised only).
- A document that exists in only one language keeps that language and is
  flagged `translation_status: "missing"`. The site shows it in its
  original language with a visible notice. **No translation is invented.**
- The six transformer test procedures (T-022, T-024, T-024-ter, T-025,
  T-026, T-027) are the exception: five already had complete Arabic HTML
  versions in the original repo (`arabic_web/.../new_translated/`) and
  were migrated as-is; **T-024-ter had no Arabic version anywhere**, so a
  faithful technical Arabic translation was created in v2
  (`tools/translate_t024_ter.py`, reviewed against the T-024 Arabic
  terminology). See `MIGRATION_REPORT.md` § "The six transformer tests".

## ما لم يتم ترحيله / What was NOT migrated

- FrontPage metadata (`_vti_cnf`, 7,634 files) — editor bookkeeping, not content.
- `scratch/` (80 Python working scripts) — the authors' working tools, not
  published documents. The v1 `chat_server.py` / `build_index.py` logic is
  replaced by `server.py` / `tools/migrate.py` here.
- Binary Office files (`.doc` / `.xls` / `.ppt`, 88 files) — not converted;
  listed in the report. Their content is not in `content/`.
- 1,199 image references (of 4,740) could not be resolved to a file in v1
  (wrong relative paths, `*_files/` folders, or files that do not exist);
  the 2,925 that resolved were copied. See `site/dist/build_log.json`.
- 15 documents have no extractable text (image-only drawings / charts and
  blank forms); they are kept as documents with their metadata and source
  path, flagged in the report.
