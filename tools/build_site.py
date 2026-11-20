#!/usr/bin/env python3
"""Build the MPIS v2 static site from content/*.json into site/dist/.

Stdlib only. Run:  python3 tools/build_site.py [--content content] [--dist site/dist]

Generates:
  dist/index.html            home page (stats, categories, search, featured tests)
  dist/categories/<cat>.html one listing page per category
  dist/docs/<id>.html        one page per document (4,525)
  dist/search.json           title/excerpt search index (client-side search)
  dist/assets/style.css      shared stylesheet (dark/light, RTL/LTR, print)
  dist/assets/app.js         theme + language switcher + live search
  dist/build_log.json        counts and any broken image links found

Images: only images actually referenced by a migrated document and found
on disk in the v1 repo are copied (deduplicated by content hash) into
dist/assets/img/. Unresolvable references are listed in the build log.
No PDF file is ever copied or generated.
"""
import argparse, hashlib, html as htmlmod, json, os, re, shutil, sys
from urllib.parse import unquote

V1_ROOT = "/home/hatch/workspace/mpis-work/repo"
FEATURED = ["T-022-R0", "T-024-R0", "T-024-R0-TER", "T-025-R0", "T-026-R0", "T-027-R0"]

CATEGORY_AR = {
    "transformers": "المحولات", "boilers": "الغلايات", "turbines": "التوربينات",
    "generators": "المولدات", "switchgear": "قواطع ومعدات التبديل",
    "protection": "الوقاية", "motors": "المحركات", "pumps": "المضخات",
    "valves": "الصمامات", "cranes": "الأوناش", "fans": "المراوح",
    "filters": "المرشحات", "instruments": "الأجهزة والتحكم",
    "substations": "محطات المحولات", "distribution": "التوزيع والنقل",
    "coordinators": "المنسقون", "forms": "النماذج", "whatsnew": "ما هو الجديد",
    "tech_resource": "الموارد الفنية", "admin_inst": "التعليمات الإدارية",
    "draft_documents": "مسودة المستندات", "quality_control": "مراقبة الجودة",
    "about": "عن النظام", "gen_docs": "مستندات عامة", "arabic_web": "صفحات عربية",
    "appr_docs": "مستندات معتمدة", "distr_trans": "التوزيع والنقل",
    "general": "عام", "index_htm": "عام",
}


def esc(s):
    return htmlmod.escape(str(s or ""), quote=True)


def base_no(no):
    return re.sub(r"(-R\d+)A$", r"\1", (no or "").upper())


def load_i18n(root):
    out = {}
    for lang in ("ar", "en"):
        with open(os.path.join(root, "i18n", lang + ".json"), encoding="utf-8") as f:
            out[lang] = json.load(f)
    return out


CSS = """/* MPIS v2 — modern, responsive, RTL/LTR, dark/light, print-friendly */
:root{--bg:#f6f7f9;--surface:#fff;--surface-2:#eef1f4;--text:#16202b;--muted:#5b6b7a;
--border:#dbe2e8;--accent:#0b5cad;--accent-2:#0e7a5f;--warn:#8a5a00;--warn-bg:#fff4d6;
--radius:14px;--shadow:0 2px 10px rgba(16,32,43,.08)}
[data-theme="dark"]{--bg:#10161d;--surface:#18222c;--surface-2:#212e3a;--text:#e8eef3;
--muted:#9fb0bf;--border:#2c3c4a;--accent:#6db3ff;--accent-2:#4cc2a0;--warn:#ffcf5c;--warn-bg:#3a2f10;
--shadow:0 2px 12px rgba(0,0,0,.35)}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI",Tahoma,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.7}
[dir="rtl"] body{font-family:"Segoe UI",Tahoma,Arial,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1060px;margin:0 auto;padding:0 18px}
.topbar{background:var(--surface);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:10}
.topbar .wrap{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
.brand{font-weight:700;font-size:1.15rem;text-decoration:none;color:var(--text)}
.controls{display:flex;gap:8px;flex-wrap:wrap}
button,.btn{cursor:pointer;border:1px solid var(--border);background:var(--surface-2);color:var(--text);
border-radius:999px;padding:7px 14px;font-size:.9rem;text-decoration:none;display:inline-block}
button:hover,.btn:hover{border-color:var(--accent)}
.hero{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;border-radius:var(--radius);
padding:28px;margin:22px 0;box-shadow:var(--shadow)}
.hero h1{margin:.2em 0;font-size:1.7rem;line-height:1.4}
.hero p{margin:.3em 0;opacity:.95}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;text-align:center;box-shadow:var(--shadow)}
.stat b{display:block;font-size:1.6rem}
.stat span{color:var(--muted);font-size:.9rem}
.searchbox{display:flex;gap:8px;margin:18px 0}
.searchbox input{flex:1;padding:12px 16px;border:1px solid var(--border);border-radius:999px;font-size:1rem;background:var(--surface);color:var(--text)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;box-shadow:var(--shadow);text-decoration:none;color:var(--text);display:block}
.card:hover{border-color:var(--accent)}
.card h3{margin:.1em 0;font-size:1.05rem}
.card p{margin:.2em 0;color:var(--muted);font-size:.88rem}
.badge{display:inline-block;font-size:.78rem;border-radius:999px;padding:2px 10px;background:var(--surface-2);border:1px solid var(--border)}
.badge.ok{background:#e3f4ec;color:#0e7a5f;border-color:#bfe6d4}
[data-theme="dark"] .badge.ok{background:#14382a;color:#4cc2a0}
.badge.warn{background:var(--warn-bg);color:var(--warn)}
.notice{background:var(--warn-bg);border:1px solid var(--border);border-radius:var(--radius);padding:12px 16px;margin:16px 0}
.doc-meta{color:var(--muted);font-size:.9rem;display:flex;gap:14px;flex-wrap:wrap;margin:8px 0}
.doc-body{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:22px;box-shadow:var(--shadow);margin:16px 0}
.doc-body h2{border-bottom:2px solid var(--accent);padding-bottom:6px}
.doc-body h3{color:var(--accent-2)}
.doc-body table{border-collapse:collapse;width:100%;margin:12px 0;display:block;overflow-x:auto}
.doc-body th,.doc-body td{border:1px solid var(--border);padding:7px 10px;text-align:start;vertical-align:top}
.doc-body th{background:var(--surface-2)}
.doc-body ul{padding-inline-start:22px}
.doc-body img{max-width:100%;height:auto;border:1px solid var(--border);border-radius:8px}
.page-label{color:var(--muted);font-size:.85rem;border-top:1px dashed var(--border);padding-top:10px;margin-top:18px}
footer{color:var(--muted);font-size:.88rem;padding:26px 0 40px}
.results{list-style:none;padding:0}
.results li{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px;margin:8px 0}
.results li a{text-decoration:none;font-weight:600}
@media print{.topbar,.controls,.searchbox,.noprint{display:none!important}body{background:#fff;color:#000}.doc-body{box-shadow:none;border:none}}
@media (max-width:640px){.hero h1{font-size:1.3rem}.doc-body{padding:14px}}
"""

JS = """// MPIS v2 — theme, language UI strings, live search
const I18N = window.MPIS_I18N || {};
let lang = localStorage.getItem('mpis-lang') || document.documentElement.lang || 'ar';
let theme = localStorage.getItem('mpis-theme') || 'light';
function applyTheme(){document.documentElement.setAttribute('data-theme',theme);
  const b=document.getElementById('themeBtn'); if(b) b.textContent=(theme==='dark'?'☀️ ':'🌙 ')+(I18N[lang]?(theme==='dark'?I18N[lang].theme_light:I18N[lang].theme_dark):'');}
function applyLang(l){lang=l; localStorage.setItem('mpis-lang',l);
  document.documentElement.lang=l; document.documentElement.dir=(l==='ar'?'rtl':'ltr');
  document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n');
    if(I18N[l]&&I18N[l][k]) el.textContent=I18N[l][k];});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{const k=el.getAttribute('data-i18n-ph');
    if(I18N[l]&&I18N[l][k]) el.placeholder=I18N[l][k];});
  const sw=document.getElementById('langBtn'); if(sw) sw.textContent=(l==='ar'?'English':'العربية');
  applyTheme();}
document.addEventListener('DOMContentLoaded',()=>{
  document.documentElement.setAttribute('data-theme',theme);
  const t=document.getElementById('themeBtn'); if(t) t.addEventListener('click',()=>{theme=(theme==='dark'?'light':'dark');localStorage.setItem('mpis-theme',theme);applyTheme();});
  const s=document.getElementById('langBtn'); if(s) s.addEventListener('click',()=>{applyLang(lang==='ar'?'en':'ar');});
  applyLang(lang);
  const input=document.getElementById('q');
  if(input){ input.addEventListener('input',()=>doSearch(input.value)); }
});
let SEARCH_INDEX=null;
async function loadIndex(){ if(SEARCH_INDEX) return SEARCH_INDEX;
  const r=await fetch('assets/search.json'); SEARCH_INDEX=await r.json(); return SEARCH_INDEX; }
async function doSearch(q){
  const box=document.getElementById('results'); if(!box) return;
  q=(q||'').trim().toLowerCase();
  if(q.length<2){ box.innerHTML=''; return; }
  const idx=await loadIndex();
  const hits=idx.filter(d=>((d.t_en||'')+' '+(d.t_ar||'')+' '+(d.n||'')+' '+(d.c||'')+' '+(d.x||'')).toLowerCase().includes(q)).slice(0,30);
  const L=I18N[lang]||{};
  box.innerHTML = hits.length
    ? '<p>'+hits.length+' '+(L.results||'results')+'</p><ul class="results">'+hits.map(d=>
        '<li><a href="docs/'+d.id+'.html">'+escHtml(d.n?d.n+' — ':'')+escHtml(lang==='ar'?(d.t_ar||d.t_en):(d.t_en||d.t_ar))+'</a><br><small>'+escHtml(d.c||'')+'</small></li>').join('')+'</ul>'
    : '<p>'+(L.no_results||'No matching results.')+'</p>';
}
function escHtml(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
"""


def render_sections(doc):
    out = []
    for s in doc.get("sections", []):
        t = s.get("type")
        if t == "heading":
            lvl = min(6, max(2, int(s.get("level", 2))))
            out.append(f"<h{lvl}>{esc(s.get('text',''))}</h{lvl}>")
        elif t == "paragraph":
            if s.get("text"):
                out.append(f"<p>{esc(s['text'])}</p>")
        elif t == "list":
            items = "".join(f"<li>{esc(i)}</li>" for i in s.get("items", []))
            if items:
                out.append(f"<ul>{items}</ul>")
        elif t == "table":
            rows = s.get("rows", [])
            if rows:
                body = ""
                for i, row in enumerate(rows):
                    tag = "th" if i == 0 else "td"
                    body += "<tr>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in row) + "</tr>"
                out.append(f"<table>{body}</table>")
                if s.get("truncated_rows"):
                    out.append(f"<p class='page-label'>Table truncated in extraction: "
                               f"{s['truncated_rows']} further rows in the original.</p>")
        elif t == "page":
            out.append(f"<div class='page-label'>Page {s.get('page')}</div>")
            for para in (s.get("text") or "").split("\n"):
                if para.strip():
                    out.append(f"<p>{esc(para)}</p>")
    if not out:
        out.append("<p><em>No extractable text in the original file "
                   "(image-only page, chart or form). See the source path below.</em></p>")
    return "\n".join(out)


def build(content_dir, dist_dir, v1_root):
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(os.path.join(dist_dir, "docs"), exist_ok=True)
    os.makedirs(os.path.join(dist_dir, "categories"), exist_ok=True)
    os.makedirs(os.path.join(dist_dir, "assets", "img"), exist_ok=True)
    i18n = load_i18n(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(content_dir, "index.json"), encoding="utf-8") as f:
        manifest = json.load(f)["documents"]
    # pairing by base doc number
    by_base = {}
    for m in manifest:
        by_base.setdefault(base_no(m.get("doc_number")), []).append(m)
    pairs = {}
    for base, ms in by_base.items():
        langs = {}
        for m in ms:
            langs.setdefault(m["language"], m)
        for m in ms:
            other = langs.get("ar" if m["language"] == "en" else "en")
            if other and other["id"] != m["id"]:
                pairs[m["id"]] = other["id"]
    # image copying (dedupe by hash)
    img_map = {}
    img_missing = []
    img_copied = 0

    def resolve_image(doc, ref):
        src = unquote(ref.get("src", ""))
        if not src or src.startswith(("http", "data:", "#")):
            return None
        doc_dir = os.path.dirname(os.path.join(v1_root, doc["source_path"]))
        cand = os.path.normpath(os.path.join(doc_dir, src))
        if not os.path.isfile(cand):
            return None
        return cand

    def doc_html(doc, other_id):
        lang = doc["language"]
        other = None
        if other_id:
            other = next((m for m in manifest if m["id"] == other_id), None)
        title = (doc.get("title_ar") if lang == "ar" else doc.get("title_en")) or \
                doc.get("title_en") or doc.get("title_ar") or doc.get("doc_number") or doc["id"]
        title = " ".join(str(title).split())
        status = doc.get("translation_status", "missing")
        badge = ("<span class='badge ok'>✓ " +
                 esc(i18n["en"]["translation_available"] + " / " + i18n["ar"]["translation_available"]) +
                 "</span>") if status == "available" else \
                ("<span class='badge warn'>" + esc(i18n["en"]["translation_partial"] + " / " +
                 i18n["ar"]["translation_partial"]) + "</span>") if status == "partial" else \
                ("<span class='badge warn'>" + esc(i18n["en"]["translation_missing"] + " / " +
                 i18n["ar"]["translation_missing"]) + "</span>")
        other_link = ""
        other_lang = "ar" if lang == "en" else "en"
        trans_sections = doc.get("sections_" + other_lang)
        trans_title = doc.get("title_" + other_lang) or ""
        is_draft = str(doc.get("translation_review", "")).startswith("draft")
        if other:
            other_link = (f"<a class='btn' href='{other['id']}.html'>🌐 " +
                          esc(i18n["en"]["view_other_language"] + " / " +
                              i18n["ar"]["view_other_language"]) + "</a>")
        elif trans_sections:
            other_link = (f"<button class='btn' type='button' id='transToggle' "
                          f"data-label-translation='🌐 {esc(i18n['en']['view_translation'] + ' / ' + i18n['ar']['view_translation'])}' "
                          f"data-label-original='🌐 {esc(i18n['en']['view_original'] + ' / ' + i18n['ar']['view_original'])}' "
                          f"onclick='toggleTranslation()'>🌐 " +
                          esc(i18n["en"]["view_translation"] + " / " +
                              i18n["ar"]["view_translation"]) + "</button>")
        else:
            other_link = ("<div class='notice'>" +
                          esc(i18n["en"]["no_other_language"] + " — " +
                              i18n["ar"]["no_other_language"]) + "</div>")
        draft_note = ""
        if is_draft:
            draft_note = ("<div class='notice'>⚠️ " +
                          esc(i18n["en"]["translation_draft_note"] + " / " +
                              i18n["ar"]["translation_draft_note"]) + "</div>")
        imgs = ""
        seen_imgs = []
        for ref in doc.get("images", [])[:20]:
            cand = resolve_image(doc, ref)
            if cand is None:
                img_missing.append({"doc": doc["id"], "src": ref.get("src", "")})
                continue
            h = hashlib.sha256(open(cand, "rb").read()).hexdigest()[:12]
            ext = os.path.splitext(cand)[1].lower() or ".jpg"
            name = h + ext
            if name not in img_map:
                shutil.copyfile(cand, os.path.join(dist_dir, "assets", "img", name))
                img_map[name] = cand
            seen_imgs.append((name, ref.get("alt", "")))
        nonlocal img_copied
        img_copied = len(img_map)
        if seen_imgs:
            imgs = "<h2>Diagrams / الرسوم</h2>" + "".join(
                f"<figure><img src='../assets/img/{n}' alt='{esc(a)}'>"
                f"<figcaption>{esc(a)}</figcaption></figure>" for n, a in seen_imgs)
        trans_body = ""
        trans_script = ""
        if trans_sections:
            trans_title_clean = " ".join(str(trans_title).split())
            trans_body = (f"<div class='doc-body' id='doc-translated' lang='{other_lang}' "
                          f"dir='{'rtl' if other_lang == 'ar' else 'ltr'}' hidden>"
                          f"<h2>{esc(trans_title_clean)}</h2>"
                          f"{render_sections({'sections': trans_sections})}{imgs}</div>")
            trans_script = ("<script>\n"
                "function toggleTranslation(){\n"
                "  var o=document.getElementById('doc-original'),"
                " t=document.getElementById('doc-translated'),"
                " b=document.getElementById('transToggle');\n"
                "  var showingTrans=t.hidden;\n"
                "  t.hidden=!showingTrans; o.hidden=showingTrans;\n"
                "  b.textContent=showingTrans?b.getAttribute('data-label-original')"
                ":b.getAttribute('data-label-translation');\n"
                "}\n</script>")
        return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{'rtl' if lang == 'ar' else 'ltr'}" data-theme="light">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — MPIS v2</title>
<link rel="stylesheet" href="../assets/style.css">
<script>window.MPIS_I18N={json.dumps(i18n, ensure_ascii=False)};</script>
<script src="../assets/app.js" defer></script></head>
<body><header class="topbar"><div class="wrap">
<a class="brand" href="../index.html">⚡ MPIS v2</a>
<div class="controls"><button id="langBtn" type="button">English</button>
<button id="themeBtn" type="button">🌙</button>
<button type="button" onclick="window.print()">🖨️ <span data-i18n="print">Print</span></button></div>
</div></header>
<main class="wrap">
<p class="noprint"><a href="../index.html" data-i18n="home">Home</a> ›
<a href="../categories/{esc(doc['category'])}.html">{esc(doc['category'])}</a></p>
<h1>{esc(title)}</h1>
<div class="doc-meta"><span><b>{esc(i18n['en']['doc_number'])}</b> {esc(doc.get('doc_number') or '—')}</span>
<span><b>{esc(i18n['en']['category'])}</b> {esc(doc['category'])}</span>
<span><b>{esc(i18n['en']['source'])}</b> <code>{esc(doc['source_path'])}</code></span>
<span>{badge}</span></div>
{other_link}
{draft_note}
<div class="doc-body" id="doc-original">{render_sections(doc)}{imgs}</div>
{trans_body}
<p class="doc-meta">Source type: {esc(doc.get('source_type',''))}
· Language: {esc(doc.get('language',''))}
· Languages available: {esc(', '.join(doc.get('languages_available', [])))}</p>
</main>
<footer><div class="wrap"><span data-i18n="footer_note">Content transcribed verbatim from the original MPIS repository.</span></div></footer>
{trans_script}
</body></html>"""

    # ---- doc pages ----
    search_index = []
    for m in manifest:
        with open(os.path.join(content_dir, m["id"] + ".json"), encoding="utf-8") as f:
            doc = json.load(f)
        with open(os.path.join(dist_dir, "docs", m["id"] + ".html"), "w", encoding="utf-8") as f:
            f.write(doc_html(doc, pairs.get(m["id"])))
        # excerpt: start of the original text plus, where an in-file draft
        # translation exists, the start of it so the translation is
        # searchable too (deep terms remain findable on the doc page)
        _orig = (doc.get("text") or "").replace("\n", " ")[:800]
        _trans = (doc.get("text_ar") or doc.get("text_en") or "").replace("\n", " ")[:400]
        search_index.append({
            "id": m["id"], "n": m.get("doc_number") or "",
            "t_en": (m.get("title_en") or "")[:160],
            "t_ar": (m.get("title_ar") or "")[:160],
            "c": m.get("category") or "",
            "x": (_orig + " " + _trans).strip(),
        })
    with open(os.path.join(dist_dir, "assets", "search.json"), "w", encoding="utf-8") as f:
        json.dump(search_index, f, ensure_ascii=False)

    # ---- categories ----
    cats = {}
    for m in manifest:
        cats.setdefault(m["category"], []).append(m)
    for cat, ms in sorted(cats.items()):
        rows = "".join(
            f"<li><a href='../docs/{m['id']}.html'>{esc((m.get('doc_number') or '') + ' — ' + ((m.get('title_ar') or m.get('title_en') or m['id'])) )}</a> "
            f"<span class='badge'>{esc(m['language'])}</span></li>" for m in sorted(ms, key=lambda x: x["id"]))
        label = CATEGORY_AR.get(cat, cat)
        with open(os.path.join(dist_dir, "categories", cat + ".html"), "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html><html lang="ar" dir="rtl" data-theme="light">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(label)} — MPIS v2</title><link rel="stylesheet" href="../assets/style.css">
<script>window.MPIS_I18N={json.dumps(i18n, ensure_ascii=False)};</script>
<script src="../assets/app.js" defer></script></head>
<body><header class="topbar"><div class="wrap"><a class="brand" href="../index.html">⚡ MPIS v2</a>
<div class="controls"><button id="langBtn" type="button">English</button>
<button id="themeBtn" type="button">🌙</button></div></div></header>
<main class="wrap"><p><a href="../index.html" data-i18n="home">Home</a></p>
<h1>{esc(label)} ({len(ms)})</h1><ul class="results">{rows}</ul></main>
<footer><div class="wrap"><span data-i18n="footer_note"></span></div></footer></body></html>""")

    # ---- home ----
    total = len(manifest)
    both = sum(1 for m in manifest if m.get("translation_status") == "available")
    missing = sum(1 for m in manifest if m.get("translation_status") == "missing")
    cat_cards = "".join(
        f"<a class='card' href='categories/{esc(cat)}.html'><h3>{esc(CATEGORY_AR.get(cat, cat))}</h3>"
        f"<p>{esc(cat)} — {len(ms)} {esc(i18n['en']['documents'])}</p></a>"
        for cat, ms in sorted(cats.items(), key=lambda kv: -len(kv[1])))
    feat = ""
    for no in FEATURED:
        ms = [m for m in manifest if (m.get("doc_number") or "").upper().startswith(no)]
        en = next((m for m in ms if m["language"] == "en"), None)
        if en:
            feat += (f"<a class='card' href='docs/{en['id']}.html'><h3>{esc(no)}</h3>"
                     f"<p>{esc((en.get('title_en') or '')[:120])}</p></a>")
    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html><html lang="ar" dir="rtl" data-theme="light">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MPIS v2 — نظام معلومات إجراءات الصيانة</title>
<link rel="stylesheet" href="assets/style.css">
<script>window.MPIS_I18N={json.dumps(i18n, ensure_ascii=False)};</script>
<script src="assets/app.js" defer></script></head>
<body><header class="topbar"><div class="wrap"><a class="brand" href="index.html">⚡ MPIS v2</a>
<div class="controls"><button id="langBtn" type="button">English</button>
<button id="themeBtn" type="button">🌙</button></div></div></header>
<main class="wrap">
<section class="hero"><p>{esc(i18n['ar']['org_line1'])} — {esc(i18n['ar']['org_line2'])}</p>
<h1 data-i18n="site_title">نظام معلومات إجراءات الصيانة</h1>
<p>Maintenance Procedure Information System — MPIS</p>
<p>{esc(i18n['ar']['org_line3'])}</p></section>
<div class="stats">
<div class="stat"><b>{total}</b><span data-i18n="stats_docs">documents</span></div>
<div class="stat"><b>{len(cats)}</b><span data-i18n="stats_categories">categories</span></div>
<div class="stat"><b>{both}</b><span data-i18n="stats_translated">documents with both languages</span></div>
<div class="stat"><b>{missing}</b><span data-i18n="stats_missing">documents without a translation yet</span></div>
</div>
<div class="searchbox"><input id="q" type="search" data-i18n-ph="search_placeholder" placeholder="ابحث في المستندات…">
<button type="button" onclick="doSearch(document.getElementById('q').value)" data-i18n="search_button">بحث</button></div>
<div id="results"></div>
<h2 data-i18n="featured_tests">إجراءات اختبار المحولات — المترجمة بالكامل</h2>
<div class="grid">{feat}</div>
<h2 data-i18n="categories">الأقسام</h2>
<div class="grid">{cat_cards}</div>
<h2 data-i18n="about_migration">عن هذه النسخة</h2>
<p data-i18n="about_migration_text"></p>
<p><a href="docs/arabic-web-ar-appr-docs-ar-ad-subst-ad-ss-docs-new-translated-t-022-r0a-htm.html">T-022-r0a (Arabic)</a> ·
<a href="docs/appr-docs-ad-subst-ad-sub-tp-t-022-r0-pdf.html">T-022-r0 (English PDF text)</a></p>
</main>
<footer><div class="wrap"><span data-i18n="footer_note"></span></div></footer>
</body></html>""")

    with open(os.path.join(dist_dir, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    with open(os.path.join(dist_dir, "assets", "app.js"), "w", encoding="utf-8") as f:
        f.write(JS)
    log = {"documents": total, "categories": len(cats), "paired_docs": len(pairs),
           "images_copied": len(img_map), "image_refs_unresolved": len(img_missing),
           "search_entries": len(search_index)}
    with open(os.path.join(dist_dir, "build_log.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": log, "image_refs_unresolved_sample": img_missing[:50]},
                  f, ensure_ascii=False, indent=1)
    print(json.dumps(log, indent=2))
    return log


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default="content")
    ap.add_argument("--dist", default="site/dist")
    a = ap.parse_args()
    build(a.content, a.dist, V1_ROOT)
