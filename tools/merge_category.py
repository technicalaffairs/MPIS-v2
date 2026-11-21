#!/usr/bin/env python3
"""Merge one category's draft translations into content/*.json + content/index.json.

Usage: python3 tools/merge_category.py --category protection \
    --ids-files translation_slices/protection_slice0.txt translation_slices/protection_slice1.txt translation_slices/protection_slice2.txt \
    [--skip <id> ...]

For each doc id:
  - load tools/translation41/<id>.translation.json and content/<id>.json
  - assert source language matches, sections_target mirrors source sections
    (same count, same types, same order), target fields are still empty
  - fill title_<other>, sections_<other>, text_<other>,
    languages_available ["en","ar"], translation_status "available",
    translation_review "draft — needs human review before operational use"
  - update the manifest entry the same way
Docs whose translation file is a same-language pass-through (target text in
the source language) are refused and listed as skipped — never merge a fake
translation. Original-language fields are never touched.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
TDIR = os.path.join(ROOT, "tools", "translation41")
REVIEW = "draft — needs human review before operational use"


def has_arabic(s):
    return any("\u0600" <= ch <= "\u06ff" for ch in (s or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True)
    ap.add_argument("--ids-files", nargs="+", required=True)
    ap.add_argument("--skip", nargs="*", default=[])
    args = ap.parse_args()

    ids = []
    for f in args.ids_files:
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            ids += [l.strip() for l in fh if l.strip()]
    ids = sorted(set(ids))
    skip = set(args.skip)

    with open(os.path.join(CONTENT, "index.json"), encoding="utf-8") as fh:
        index = json.load(fh)
    manifest = {m["id"]: m for m in index["documents"]}

    merged, skipped, total_words = [], [], 0
    for doc_id in ids:
        if doc_id in skip:
            skipped.append((doc_id, "explicitly skipped"))
            continue
        tr_path = os.path.join(TDIR, doc_id + ".translation.json")
        if not os.path.exists(tr_path):
            skipped.append((doc_id, "no translation file (untranslatable — no fake pass-through written)"))
            continue
        with open(tr_path, encoding="utf-8") as fh:
            tr = json.load(fh)
        with open(os.path.join(CONTENT, doc_id + ".json"), encoding="utf-8") as fh:
            doc = json.load(fh)
        src_lang = tr["source_language"]
        if doc["language"] != src_lang:
            skipped.append((doc_id, f"language mismatch doc={doc['language']} tr={src_lang}"))
            continue
        if len(tr["sections_target"]) != len(doc["sections"]) or any(
                a["type"] != b["type"] for a, b in zip(tr["sections_target"], doc["sections"])):
            skipped.append((doc_id, "sections_target does not mirror source sections"))
            continue
        other = "ar" if src_lang == "en" else "en"
        if doc.get("title_" + other, "") not in ("", None) or ("sections_" + other) in doc:
            skipped.append((doc_id, "target fields already present"))
            continue
        # refuse same-language pass-throughs: target text must be in the other language
        # (verbatim team-number codes like "أ1".."أ20" are source codes kept as-is
        # and must not count as Arabic content — forms WOF-002 / QCD-024, 2026-11-20;
        # likewise isolated single Arabic letters, e.g. a lone "ا" source fragment
        # kept verbatim in instruments TIMP-001, 2026-11-20, or a trailing "د،"
        # fragment in degraded arabic_web scans EFR-002/003/004, OCR-007/008,
        # 2026-11-20 — a real pass-through contains multi-letter Arabic words,
        # which this still catches. Note: the "isolated" test must ignore Arabic
        # punctuation (،) next to the letter, so it uses the Arabic LETTER ranges,
        # not the whole Arabic block.)
        import re as _re
        _AR_LETTER = r"[\u0621-\u064a\u066e-\u06d3\u06fa-\u06fc\u06ff]"
        tgt_text = (tr.get("text_target") or "")[:2000]
        tgt_text_check = _re.sub(r"أ\d+", "", tgt_text)
        tgt_text_check = _re.sub(
            r"(?<!" + _AR_LETTER + r")" + _AR_LETTER + r"(?!" + _AR_LETTER + r")",
            "", tgt_text_check)
        # NB: the EN-target check below tests for Arabic LETTERS, not any char in
        # the Arabic block — a lone Arabic comma "،" left behind after stripping
        # an isolated "د" fragment is punctuation, not content.
        if other == "ar" and not has_arabic(tgt_text):
            skipped.append((doc_id, "target text has no Arabic (pass-through?)"))
            continue
        if other == "en" and _re.search(_AR_LETTER, tgt_text_check):
            skipped.append((doc_id, "target text is Arabic but target is English (pass-through?)"))
            continue
        doc["title_" + other] = tr["title_target"]
        doc["sections_" + other] = tr["sections_target"]
        doc["text_" + other] = tr["text_target"]
        doc["languages_available"] = ["en", "ar"]
        doc["translation_status"] = "available"
        doc["translation_review"] = REVIEW
        with open(os.path.join(CONTENT, doc_id + ".json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        m = manifest[doc_id]
        m["title_" + other] = tr["title_target"]
        m["translation_status"] = "available"
        total_words += tr["word_count_source"]
        merged.append(doc_id)

    with open(os.path.join(CONTENT, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)

    print(f"merged {len(merged)} docs, {total_words:,} source words")
    for doc_id, why in skipped:
        print(f"SKIPPED {doc_id}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
