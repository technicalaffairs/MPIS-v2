#!/usr/bin/env python3
"""Merge the 34 draft re-translations (tools/translation41/*.translation.json)
into content/<id>.json and content/index.json.

Second pass: after the table-extraction fix in tools/migrate.py (<p> inside
<td> no longer leaks cell text), content/ was re-migrated and the 34
translations were rebuilt against the NEW section structure. The other 7
docs of the original 41 batch — the Boilers/Fans/Filters/Generators/Motors/
Pumps/Valves index pages — are now genuinely paired with Arabic originals
and needed no draft translation.

For each doc:
  - en source: title_ar / sections_ar / text_ar = translation
  - ar source: title_en / sections_en / text_en = translation
  - languages_available = ["en", "ar"]; translation_status = "available"
  - translation_review = "draft — needs human review before operational use"
Original-language fields (title/sections/text in the source language) are
never touched. Manifest entries get the translated title + status only.

Also writes TRANSLATION_41.md at the repo root.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTENT = os.path.join(ROOT, "content")
TDIR = os.path.join(ROOT, "tools", "translation41")
REVIEW = "draft — needs human review before operational use"
CATS = {"pumps", "generators", "fans", "filters", "valves", "motors", "boilers"}


def main():
    with open(os.path.join(CONTENT, "index.json"), encoding="utf-8") as f:
        index = json.load(f)
    manifest = {m["id"]: m for m in index["documents"]}
    want = [m["id"] for m in index["documents"]
            if m["category"] in CATS and m["translation_status"] == "missing"]
    assert len(want) == 34, f"expected 34 missing docs, found {len(want)}"

    rows = []
    total_words = 0
    for doc_id in sorted(want):
        with open(os.path.join(TDIR, doc_id + ".translation.json"), encoding="utf-8") as f:
            tr = json.load(f)
        with open(os.path.join(CONTENT, doc_id + ".json"), encoding="utf-8") as f:
            doc = json.load(f)
        src_lang = tr["source_language"]
        assert doc["language"] == src_lang, (doc_id, doc["language"], src_lang)
        assert len(tr["sections_target"]) == len(doc["sections"]), doc_id
        for a, b in zip(tr["sections_target"], doc["sections"]):
            assert a["type"] == b["type"], (doc_id, a["type"], b["type"])
        other = "ar" if src_lang == "en" else "en"
        # original-language fields must already be intact; only fill the other side
        assert doc.get("title_" + other, "") in ("", None), (doc_id, "title already present")
        assert ("sections_" + other) not in doc and ("text_" + other) not in doc, doc_id
        doc["title_" + other] = tr["title_target"]
        doc["sections_" + other] = tr["sections_target"]
        doc["text_" + other] = tr["text_target"]
        doc["languages_available"] = ["en", "ar"]
        doc["translation_status"] = "available"
        doc["translation_review"] = REVIEW
        with open(os.path.join(CONTENT, doc_id + ".json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        m = manifest[doc_id]
        m["title_" + other] = tr["title_target"]
        m["translation_status"] = "available"
        total_words += tr["word_count_source"]
        rows.append({
            "id": doc_id, "doc_number": tr.get("doc_number") or doc.get("doc_number") or "",
            "category": tr["category"], "source": src_lang,
            "words": tr["word_count_source"], "uncertain": tr.get("uncertain_terms", []),
        })

    with open(os.path.join(CONTENT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    # ---- TRANSLATION_41.md ----
    lines = []
    lines.append("# The 34 re-translations — pumps, generators, fans, filters, valves, motors, boilers")
    lines.append("")
    lines.append("**Status: DRAFT — every translation below needs human review before operational use.**")
    lines.append("Each translated document carries `translation_review: \"draft — needs human review before operational use\"`")
    lines.append("in its `content/<id>.json`, and the rendered site shows a visible draft notice on those pages.")
    lines.append("Original-language text was not changed. No content was added, deleted or softened;")
    lines.append("empty record-sheet fields were left empty.")
    lines.append("")
    lines.append("Second pass, after the table-extraction fix in `tools/migrate.py` (`<p>` inside `<td>` no")
    lines.append("longer leaks cell text): `content/` was re-migrated and these 34 translations were rebuilt")
    lines.append("against the new section structure. The other 7 documents of the original 41 — the")
    lines.append("Boilers / Fans / Filters / Generators / Motors / Pumps / Valves index pages — turned out to")
    lines.append("be genuinely paired with Arabic originals after the re-migration and needed no draft translation.")
    lines.append("")
    lines.append(f"Total: **34 documents, {total_words:,} source words** — 26 English → Arabic, 8 Arabic → English.")
    lines.append("These 34 complete the bilingual coverage of 7 categories: boilers (16), motors (12), valves (4),")
    lines.append("pumps (2); generators, fans and filters are fully bilingual from genuine originals.")
    lines.append("")
    lines.append("| # | Document | Category | Source | Words | Terms / passages flagged as uncertain |")
    lines.append("|---|----------|----------|--------|------:|--------------------------------------|")
    for i, r in enumerate(rows, 1):
        unc = "; ".join(
            f"**{u.get('term','')}** — {u.get('note','')}".strip()
            for u in r["uncertain"]) or "—"
        lines.append(f"| {i} | `{r['id']}` ({r['doc_number']}) | {r['category']} | {r['source']} | {r['words']} | {unc} |")
    lines.append("")
    lines.append("## Notes for the reviewer")
    lines.append("")
    lines.append("- **G-058 / G-057 (motors):** the original repo holds two files, `G-057-r0.htm` and `G-058-r0.htm`,")
    lines.append("  whose content is identical and both labelled \"G-057-r0 APPROVED\" inside the file. Both were")
    lines.append("  translated as-is; the document number was not changed. Worth checking in the source repo whether")
    lines.append("  G-058 is a misfiled copy of G-057 or a genuinely different procedure.")
    lines.append("- **V-002-R0 (valves):** the same document is filed twice in the original repo; the Arabic version's")
    lines.append("  body is mostly already English, so only the Arabic passages were translated.")
    lines.append("- **T-024 Tests 6–7 (transformers, not part of this batch):** the Arabic appendix pages inside the")
    lines.append("  source PDFs label Tests 6–7 differently from the English text; English was used as the source of")
    lines.append("  truth when the PDFs were migrated. Confirm before operational use.")
    lines.append("- **\"Ad docs\"** in the index-page navigation bars was read as \"approved documents\" (المستندات المعتمدة);")
    lines.append("  it could also mean \"admin documents\". (Index pages needed no draft translation in this pass.)")
    lines.append("- Station names, manufacturer names, model codes, interval codes (M1/Y1/H1500…) and units were kept")
    lines.append("  in Latin script exactly as in the source, including source typos in names (e.g. `Fulid`, `Bofflo`,")
    lines.append("  `Backle`/`Balckle`, `Ugoslaf`, `Demiatta`).")
    lines.append("")
    with open(os.path.join(ROOT, "TRANSLATION_41.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"merged 34 docs, {total_words:,} source words")
    print("wrote TRANSLATION_41.md")


if __name__ == "__main__":
    main()
