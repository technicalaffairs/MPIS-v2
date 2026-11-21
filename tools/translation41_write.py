#!/usr/bin/env python3
"""Write .translation.json files from a JSON payload on stdin.
Payload: {"docs": [ {id, doc_number, category, source_language, target_language,
 title_target, sections_target, text_target, word_count_source, uncertain_terms}, ... ]}
Validates section structure mirrors the source exactly (count/order/types/keys).
"""
import json, sys, os

SRC_DIR = os.path.expanduser("~/workspace/mpis-v2/content")
OUT_DIR = os.path.expanduser("~/workspace/mpis-v2/tools/translation41")

def norm_sec(s):
    if s.get("type") == "table":
        return ("table", tuple(tuple(c for c in r) for r in s.get("rows", [])))
    if s.get("type") == "list":
        return ("list", len(s.get("items", [])))
    return (s.get("type"),)

def main():
    payload = json.load(sys.stdin)
    for doc in payload["docs"]:
        did = doc["id"]
        src = json.load(open(os.path.join(SRC_DIR, did + ".json")))
        ssecs = src.get("sections") or []
        tsecs = doc["sections_target"]
        assert len(ssecs) == len(tsecs), f"{did}: section count {len(ssecs)} vs {len(tsecs)}"
        for i, (s, t) in enumerate(zip(ssecs, tsecs)):
            assert s.get("type") == t.get("type"), f"{did} sec {i}: type {s.get('type')} vs {t.get('type')}"
            # copy non-text structural keys from source (e.g. truncated_rows)
            for k, v in s.items():
                if k not in t:
                    t[k] = v
            if s.get("type") == "table":
                assert len(s["rows"]) == len(t["rows"]), f"{did} sec {i}: table rows"
                for r1, r2 in zip(s["rows"], t["rows"]):
                    assert len(r1) == len(r2), f"{did} sec {i}: table cols"
            if s.get("type") == "list":
                assert len(s["items"]) == len(t["items"]), f"{did} sec {i}: list items"
            if "level" in s:
                assert s["level"] == t["level"], f"{did} sec {i}: level"
        # word count check
        wc = len((src.get("text") or "").split())
        assert wc == doc["word_count_source"], f"{did}: wc {wc} vs {doc['word_count_source']}"
        assert doc["doc_number"] == src.get("doc_number"), f"{did}: doc_number mismatch"
        out = {
            "id": did,
            "doc_number": doc["doc_number"],
            "category": "gen_docs",
            "source_language": doc["source_language"],
            "target_language": doc["target_language"],
            "title_target": doc["title_target"],
            "sections_target": tsecs,
            "text_target": doc["text_target"],
            "word_count_source": wc,
            "uncertain_terms": doc.get("uncertain_terms", []),
        }
        with open(os.path.join(OUT_DIR, did + ".translation.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("WROTE", did, wc, "words,", len(tsecs), "sections,", len(doc.get("uncertain_terms", [])), "uncertain")

if __name__ == "__main__":
    main()
