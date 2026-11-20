#!/usr/bin/env python3
"""MPIS v2 local server — stdlib only, no dependencies.

Serves the generated static site (site/dist) and a search API over the
migrated content. The old v1 chat_server.py called Cohere with a
hard-coded API key; that key is NOT present anywhere in this repository.
If you want the optional AI chat endpoint, set the key in the environment
only — never put it in code or in a committed file:

    export COHERE_API_KEY="..."
    python3 server.py

Without COHERE_API_KEY the server still works fully for browsing and
search; /api/chat returns 503 with an explanatory message.

Usage:
    python3 server.py [--port 8000] [--content content] [--dist site/dist]
"""
import argparse, json, os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

CONTENT = "content"
DIST = "site/dist"
COHERE_MODEL = os.environ.get("COHERE_MODEL", "command-r-08-2024")


def search_docs(query, limit=20):
    """Search titles, doc numbers, categories and the 800-char excerpt
    stored in dist/assets/search.json (built by tools/build_site.py).
    Falls back to the manifest (titles only) if the index is absent."""
    kws = [k for k in re.findall(r"\w+", query.lower()) if len(k) >= 2]
    if not kws:
        return []
    corpus_path = os.path.join(DIST, "assets", "search.json")
    entries = []
    if os.path.isfile(corpus_path):
        with open(corpus_path, encoding="utf-8") as f:
            for e in json.load(f):
                entries.append({
                    "id": e["id"], "doc_number": e.get("n") or "",
                    "title_en": e.get("t_en") or "", "title_ar": e.get("t_ar") or "",
                    "category": e.get("c") or "", "snippet": e.get("x") or "",
                    "translation_status": "", "source_path": "",
                    "language": "", "source_type": "",
                })
    else:
        with open(os.path.join(CONTENT, "index.json"), encoding="utf-8") as f:
            entries = json.load(f)["documents"]
            for e in entries:
                e["snippet"] = ""
    scored = []
    for m in entries:
        hay = " ".join([m.get("title_en") or "", m.get("title_ar") or "",
                        m.get("doc_number") or "", m.get("category") or "",
                        m.get("snippet") or ""]).lower()
        score = sum(hay.count(k) * (5 if k in (m.get("doc_number") or "").lower() else 1)
                    for k in kws)
        if score:
            scored.append((score, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:limit]]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIST, **kw)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/search":
            q = parse_qs(u.query).get("q", [""])[0]
            self._json({"query": q, "results": search_docs(q)})
            return
        if u.path == "/api/chat":
            key = os.environ.get("COHERE_API_KEY")
            if not key:
                self._json({"error": "AI chat is not configured: set COHERE_API_KEY "
                                    "in the environment. Search and browsing work "
                                    "without it."}, status=503)
                return
            self._json({"error": "AI chat via Cohere is not bundled in this "
                                "server; use the key from the environment with "
                                "your own client. Model: " + COHERE_MODEL},
                       status=501)
            return
        super().do_GET()

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # quieter logging
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--content", default="content")
    ap.add_argument("--dist", default="site/dist")
    a = ap.parse_args()
    CONTENT, DIST = a.content, a.dist
    print(f"MPIS v2 serving {DIST} on http://localhost:{a.port}/")
    print("Search API: /api/search?q=transformer")
    print("AI chat:", "configured (key from environment)" if os.environ.get("COHERE_API_KEY")
          else "not configured (set COHERE_API_KEY to enable)")
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
