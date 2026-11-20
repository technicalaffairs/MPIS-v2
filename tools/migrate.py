#!/usr/bin/env python3
"""MPIS v1 -> v2 migration: HTML (.htm/.html) and PDF -> structured JSON.

Stdlib only (no BeautifulSoup / no pip) so the converter is repeatable
anywhere Python 3.10+ and `pdftotext` (poppler) are available.

Usage:
    python3 tools/migrate.py [--source /path/to/MPIS-v1] [--out content]
    [--log migration_log.json]

Rules (faithful migration, no invention):
- Text is extracted verbatim (whitespace normalised only). Nothing is
  summarised, paraphrased or added.
- A document that exists in only one language keeps that language and is
  flagged translation_status="missing" for the other language. No fake
  translation is generated.
- PDFs are converted to text only; no PDF file is copied into v2.
- FrontPage metadata (_vti_cnf) and the scratch/ working scripts are
  excluded from content (counted in the report, not migrated as documents).
- Duplicate files (identical SHA-256, e.g. the copies in new/) are kept
  once; the duplicates are recorded in the log.
"""
import argparse, hashlib, html as htmlmod, json, os, re, subprocess, sys
from html.parser import HTMLParser

EXCLUDE_DIRS = {".git", "_vti_cnf", "scratch"}
# Top-level folders that are working material, not published content.
EXCLUDE_TOP = {"scratch"}
DOC_RE = re.compile(r"\b([A-Z]{1,4}-?\d{1,4}(?:-[A-Z0-9]+)?-r\d+[a-z]?)\b", re.I)
DOC_RE2 = re.compile(r"\b([A-Z]{1,4}-?\d{1,4})\b")

CATEGORY_LABELS = {
    "transformers": "Transformers / المحولات",
    "boilers": "Boilers / الغلايات",
    "turbines": "Turbines / التوربينات",
    "generators": "Generators / المولدات",
    "switchgear": "Switchgear / قواطع ومعدات التبديل",
    "protection": "Protection / الوقاية",
    "motors": "Motors / المحركات",
    "pumps": "Pumps / المضخات",
    "valves": "Valves / الصمامات",
    "cranes": "Cranes / الأوناش",
    "fans": "Fans / المراوح",
    "filters": "Filters / المرشحات",
    "instruments": "Instruments & Control / الأجهزة والتحكم",
    "substations": "Substations / محطات المحولات",
}


def slugify(path):
    s = re.sub(r"[^A-Za-z0-9]+", "-", path.lower()).strip("-")
    return s[:150] or "doc"


def decode_bytes(b):
    """Pick the best decoding: UTF-8 first (most new files), then
    Windows-1256 (Arabic legacy files), then Windows-1252 (Latin)."""
    s_utf = b.decode("utf-8", "replace")
    repl = s_utf.count("\ufffd")
    ar_utf = sum(1 for c in s_utf if "\u0600" <= c <= "\u06ff")
    if repl == 0:
        return s_utf, "utf-8"
    s1256 = b.decode("windows-1256", "ignore")
    ar1256 = sum(1 for c in s1256 if "\u0600" <= c <= "\u06ff")
    s1252 = b.decode("windows-1252", "ignore")
    if repl <= 5 and ar_utf > 20:
        # a few stray bytes in an otherwise good UTF-8 file
        return b.decode("utf-8", "ignore"), "utf-8-ignore"
    if ar1256 > 20:
        return s1256, "windows-1256"
    return s1252, "windows-1252"



_MOJIBAKE_MARKERS = set("\u2026\u20ac\u201a\u0192\u201e\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d\u00a5\u00ac\u00a6\u00a7\u00a8\u00a9\u00aa\u00ab\u00ae\u00af\u00b0\u00b1\u00b2\u00b3\u00b4\u00b5\u00b6\u00b7\u00b8\u00b9\u00ba\u00bb\u00bc\u00bd\u00be\u00bf\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178\u00a1\u00a2\u00a3\u00a4")

def repair_mojibake(text):
    """Repair double-encoded Arabic: UTF-8 bytes of Arabic text that were
    mis-decoded as Windows-1256 and re-saved as UTF-8 (common in the
    new_translated/ files). Only tokens containing mojibake marker
    characters are repaired; correct Arabic is left untouched."""
    def fix_token(tok):
        if not any(c in _MOJIBAKE_MARKERS for c in tok):
            return tok
        try:
            fixed = tok.encode("cp1256", "ignore").decode("utf-8", "ignore")
        except Exception:
            return tok
        if fixed and "\ufffd" not in fixed and not any(
                c in _MOJIBAKE_MARKERS for c in fixed):
            if sum(1 for c in fixed if "\u0600" <= c <= "\u06ff") >= 1:
                return fixed
        return tok
    return " ".join(fix_token(t) for t in text.split(" "))


def clean(text):
    text = text.replace("\xa0", " ")
    text = htmlmod.unescape(text)
    text = re.sub(r"[ \t\r]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


class Extractor(HTMLParser):
    """Collect title, headings, paragraphs, lists, tables, links, images."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.blocks = []          # ordered: {type, level?, text, items?, rows?}
        self.links = []
        self.images = []
        self._tag = None
        self._buf = ""
        self._in_title = False
        self._in_script_style = False
        self._list_items = None
        self._table_rows = None
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._in_script_style = True
            return
        # Inside a table cell, <p>/<h*>/<li> are just formatting wrappers
        # (FrontPage files often have unclosed <p> inside <td>); their text
        # belongs to the cell, not to a new paragraph/heading block.
        if self._cell is not None and tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol"):
            return
        if tag == "title":
            self._in_title = True
            self._buf = ""
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._tag = tag
            self._buf = ""
        elif tag == "p":
            self._tag = "p"
            self._buf = ""
        elif tag == "li":
            self._tag = "li"
            self._buf = ""
        elif tag in ("ul", "ol"):
            self._list_items = []
        elif tag == "table":
            self._table_rows = []
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = ""
            self._tag = "cell"
        elif tag == "a" and a.get("href"):
            self.links.append({"href": a["href"][:500], "text": ""})
        elif tag == "img" and a.get("src"):
            self.images.append({"src": a["src"][:500], "alt": a.get("alt", "")[:200]})

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._in_script_style = False
            return
        # Closing a formatting tag inside a cell ends nothing: the cell
        # is still open until </td>/<th>.
        if self._cell is not None and tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol"):
            return
        if tag == "title":
            self._in_title = False
            self.title = clean(self._buf)[:160]
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            t = clean(self._buf)
            if t:
                self.blocks.append({"type": "heading", "level": int(tag[1]), "text": t})
            self._tag = None
        elif tag == "p":
            t = clean(self._buf)
            if t:
                self.blocks.append({"type": "paragraph", "text": t})
            self._tag = None
        elif tag == "li":
            t = clean(self._buf)
            if t and self._list_items is not None:
                self._list_items.append(t)
            self._tag = None
        elif tag in ("ul", "ol"):
            if self._list_items:
                self.blocks.append({"type": "list", "items": self._list_items})
            self._list_items = None
        elif tag in ("td", "th"):
            if self._cell is not None and self._row is not None:
                self._row.append(clean(self._cell))
            self._cell = None
            self._tag = None
        elif tag == "tr":
            if self._row is not None and self._table_rows is not None:
                if any(c for c in self._row):
                    self._table_rows.append(self._row)
            self._row = None
        elif tag == "table":
            if self._table_rows:
                # keep tables up to 200 rows; note truncation in the doc
                self.blocks.append(
                    {"type": "table", "rows": self._table_rows[:200],
                     "truncated_rows": max(0, len(self._table_rows) - 200)})
            self._table_rows = None

    def handle_data(self, data):
        if self._in_script_style:
            return
        if self._in_title or self._tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li"):
            self._buf += data
        elif self._tag == "cell" and self._cell is not None:
            self._cell += data
        elif self.links and data.strip():
            # anchor text of the most recent link (best effort)
            if not self.links[-1]["text"]:
                self.links[-1]["text"] = clean(data)[:200]


def extract_html(path):
    raw = open(path, "rb").read()
    text, enc = decode_bytes(raw)
    ex = Extractor()
    try:
        ex.feed(text)
    except Exception:
        pass
    # Fallback title from <title> raw search
    if not ex.title:
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        if m:
            ex.title = clean(re.sub(r"<[^>]+>", "", m.group(1)))
    ex.title = repair_mojibake(ex.title)
    for b in ex.blocks:
        if "text" in b:
            b["text"] = repair_mojibake(b["text"])
        if "items" in b:
            b["items"] = [repair_mojibake(i) for i in b["items"]]
        if "rows" in b:
            b["rows"] = [[repair_mojibake(c) for c in row] for row in b["rows"]]
    def block_text(b):
        if b["type"] == "list":
            return "\n".join(b["items"])
        if b["type"] == "table":
            return "\n".join(" | ".join(row) for row in b.get("rows", []))
        return b.get("text", "")
    plain = "\n".join(block_text(b) for b in ex.blocks)
    return ex, plain, enc


def doc_number(name, title, text):
    for src in (title, name, text[:2000]):
        m = DOC_RE.search(src or "")
        if m:
            no = m.group(1).upper()
            # variant suffixes that follow the revision, e.g. T-024-r0-ter
            if re.search(r"-r\d+[a-z]?-ter\b", name or "", re.I):
                no += "-TER"
            return no
    m = DOC_RE2.search(name or "")
    return m.group(1).upper() if m else None


def category_for(rel_path):
    low = rel_path.replace("\\", "/").lower()
    keywords = [
        ("transformers", "transformers"), ("boilers", "boilers"),
        ("turbines", "turbines"), ("generators", "generators"),
        ("switchgear", "switchgear"), ("protection", "protection"),
        ("motors", "motors"), ("pumps", "pumps"), ("valves", "valves"),
        ("cranes", "cranes"), ("fans", "fans"), ("filters", "filters"),
        ("instr", "instruments"), ("sub_tp", "substations"),
        ("ad_subst", "substations"), ("substations", "substations"),
        ("distr", "distribution"), ("coordinators", "coordinators"),
        ("forms", "forms"), ("whatsnew", "whatsnew"),
        ("tech_resource", "tech_resource"), ("admin_inst", "admin_inst"),
        ("draf_docs", "draft_documents"), ("qual_cntrl", "quality_control"),
        ("about", "about"),
    ]
    for kw, cat in keywords:
        if kw in low:
            return cat
    parts = [p for p in rel_path.replace("\\", "/").split("/") if p]
    if parts:
        return re.sub(r"[^a-z0-9]+", "_", parts[0].lower())[:40]
    return "general"


def detect_lang(rel_path, text):
    ar = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    if "arabic_web" in rel_path or "/Ar_" in rel_path or rel_path.startswith("Ar_"):
        return "ar"
    if ar > 50:
        return "ar"
    return "en"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def migrate(source, outdir, log_path):
    source = os.path.abspath(source)
    os.makedirs(outdir, exist_ok=True)
    log = {"source": source, "html": {"total": 0, "migrated": 0, "empty": 0, "errors": []},
           "pdf": {"total": 0, "migrated": 0, "duplicates": [], "errors": []},
           "duplicates": [], "excluded": {}, "categories": {},
           "docs": []}
    seen_hashes = {}
    manifest = []

    # ---- HTML ----
    html_files = []
    for dp, dn, fn in os.walk(source):
        dn[:] = [d for d in dn if d not in EXCLUDE_DIRS and d != ".git"]
        rel_dp = os.path.relpath(dp, source)
        if rel_dp.split(os.sep)[0] in EXCLUDE_TOP:
            continue
        for f in fn:
            if f.lower().endswith((".htm", ".html")):
                html_files.append(os.path.join(dp, f))
    html_files.sort()
    log["html"]["total"] = len(html_files)

    for path in html_files:
        rel = os.path.relpath(path, source).replace(os.sep, "/")
        try:
            h = sha256_file(path)
            if h in seen_hashes:
                log["duplicates"].append({"path": rel, "duplicate_of": seen_hashes[h]})
                continue
            seen_hashes[h] = rel
            ex, plain, enc = extract_html(path)
            if not plain.strip() and not ex.title:
                log["html"]["empty"] += 1
                continue
            name = os.path.basename(path)
            doc_no = doc_number(name, ex.title, plain)
            lang = detect_lang(rel, plain)
            cat = category_for(rel)
            doc_id = slugify(rel)
            # cap blocks to keep JSON sane; record truncation honestly
            blocks = ex.blocks[:600]
            truncated = len(ex.blocks) > 600
            doc = {
                "id": doc_id,
                "doc_number": doc_no,
                "title_en": ex.title if lang == "en" else "",
                "title_ar": ex.title if lang == "ar" else "",
                "category": cat,
                "source_path": rel,
                "source_type": "html",
                "source_encoding": enc,
                "language": lang,
                "languages_available": [lang],
                "translation_status": "missing" if lang == "en" else "missing",
                "sections": blocks,
                "text": plain[:60000],
                "text_truncated": len(plain) > 60000 or truncated,
                "links": ex.links[:100],
                "images": ex.images[:100],
            }
            with open(os.path.join(outdir, doc_id + ".json"), "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
            manifest.append({"id": doc_id, "doc_number": doc_no,
                             "title_en": doc["title_en"], "title_ar": doc["title_ar"],
                             "category": cat, "source_path": rel, "source_type": "html",
                             "language": lang, "translation_status": "missing"})
            log["html"]["migrated"] += 1
            log["categories"][cat] = log["categories"].get(cat, 0) + 1
        except Exception as e:  # noqa: BLE001 - keep migrating the rest
            log["html"]["errors"].append({"path": rel, "error": str(e)[:300]})

    # ---- PDFs (via pdftotext -layout) ----
    pdf_files = []
    for dp, dn, fn in os.walk(source):
        dn[:] = [d for d in dn if d not in EXCLUDE_DIRS and d != ".git"]
        rel_dp = os.path.relpath(dp, source)
        if rel_dp.split(os.sep)[0] in EXCLUDE_TOP:
            continue
        for f in fn:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dp, f))
    pdf_files.sort()
    log["pdf"]["total"] = len(pdf_files)
    for path in pdf_files:
        rel = os.path.relpath(path, source).replace(os.sep, "/")
        try:
            h = sha256_file(path)
            if h in seen_hashes:
                log["pdf"]["duplicates"].append({"path": rel, "duplicate_of": seen_hashes[h]})
                log["duplicates"].append({"path": rel, "duplicate_of": seen_hashes[h]})
                continue
            seen_hashes[h] = rel
            r = subprocess.run(["pdftotext", "-layout", path, "-"],
                               capture_output=True, timeout=120)
            text = r.stdout.decode("utf-8", "ignore")
            pages = [clean(p) for p in text.split("\f")]
            pages = [p for p in pages if p]
            if not pages:
                log["pdf"]["errors"].append({"path": rel, "error": "no extractable text (scanned image PDF?)"})
                continue
            name = os.path.basename(path)
            first = pages[0][:2000]
            doc_no = doc_number(name, "", first)
            ar_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
            lang = "ar" if ar_chars > 200 else "en"
            # bilingual PDFs (English pages + Arabic pages) are flagged
            has_ar_pages = any(sum(1 for c in p if "\u0600" <= c <= "\u06ff") > 50 for p in pages)
            has_en_pages = any(sum(1 for c in p if c.isascii()) > 100 for p in pages)
            langs = []
            if has_en_pages:
                langs.append("en")
            if has_ar_pages:
                langs.append("ar")
            cat = category_for(rel)
            doc_id = slugify(rel)
            sections = [{"type": "page", "page": i + 1, "text": p} for i, p in enumerate(pages)]
            doc = {
                "id": doc_id,
                "doc_number": doc_no,
                "title_en": (pages[0].split("\n")[2].strip() if len(pages[0].split("\n")) > 2 else name),
                "title_ar": "",
                "category": cat,
                "source_path": rel,
                "source_type": "pdf",
                "source_encoding": "pdf-text",
                "language": "en" if "en" in langs else "ar",
                "languages_available": langs or [lang],
                "translation_status": "missing" if len(langs) < 2 else "partial",
                "sections": sections,
                "text": "\n".join(pages)[:60000],
                "text_truncated": len("\n".join(pages)) > 60000,
                "links": [],
                "images": [],
                "pdf_pages": len(pages),
                "pdf_has_embedded_arabic_pages": has_ar_pages and has_en_pages,
            }
            with open(os.path.join(outdir, doc_id + ".json"), "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
            manifest.append({"id": doc_id, "doc_number": doc_no,
                             "title_en": doc["title_en"], "title_ar": "",
                             "category": cat, "source_path": rel, "source_type": "pdf",
                             "language": doc["language"],
                             "translation_status": doc["translation_status"]})
            log["pdf"]["migrated"] += 1
            log["categories"][cat] = log["categories"].get(cat, 0) + 1
        except Exception as e:  # noqa: BLE001
            log["pdf"]["errors"].append({"path": rel, "error": str(e)[:300]})

    # ---- pairing: same doc_number in both languages ----
    def base_no(no):
        return re.sub(r"(-R\d+)A$", r"\1", (no or "").upper())

    by_no = {}
    for m in manifest:
        if m["doc_number"]:
            by_no.setdefault(base_no(m["doc_number"]), []).append(m)
    paired = 0
    for no, ms in by_no.items():
        langs = {m["language"] for m in ms}
        if {"en", "ar"} <= langs:
            paired += 1
            for m in ms:
                m["translation_status"] = "available"
    log["paired_doc_numbers_en_ar"] = paired
    log["docs"] = manifest
    with open(os.path.join(outdir, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"documents": manifest,
                   "categories": sorted(log["categories"].items())}, f, ensure_ascii=False, indent=1)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print(json.dumps({"html_total": log["html"]["total"], "html_migrated": log["html"]["migrated"],
                      "pdf_total": log["pdf"]["total"], "pdf_migrated": log["pdf"]["migrated"],
                      "pdf_duplicates": len(log["pdf"]["duplicates"]),
                      "duplicates_total": len(log["duplicates"]),
                      "paired": paired,
                      "html_errors": len(log["html"]["errors"]),
                      "pdf_errors": len(log["pdf"]["errors"])}, indent=2))
    return log


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="/home/hatch/workspace/mpis-work/repo")
    ap.add_argument("--out", default="content")
    ap.add_argument("--log", default="migration_log.json")
    a = ap.parse_args()
    migrate(a.source, a.out, a.log)
