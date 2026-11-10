#!/usr/bin/env python3
"""Lint a single-file HTML report for self-containment and structure.

Usage: python check_report.py report.html [--strict]
Exit code: 0 = pass (warnings allowed), 1 = failures (or warnings with --strict).
Stdlib only.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

EXTERNAL = re.compile(r"^\s*(https?:)?//", re.I)


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.headings, self.ids, self.ext = [], [], [], []
        self.has = {k: False for k in ("doctype", "lang", "charset", "viewport", "title", "main")}
        self._in_title = False
        self.title = ""

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype html"):
            self.has["doctype"] = True

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag == "html" and a.get("lang"):
            self.has["lang"] = True
        if tag == "meta":
            if "charset" in a:
                self.has["charset"] = True
            if a.get("name") == "viewport":
                self.has["viewport"] = True
        if tag == "title" and not self.title and "svg" not in self.tags:
            self._in_title = True
        if tag == "main":
            self.has["main"] = True
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if "id" in a:
            self.ids.append(a["id"])
        # External resource loads (not plain hyperlinks)
        for attr in ("src", "srcset", "poster", "data"):
            v = a.get(attr)
            if v and EXTERNAL.match(v):
                self.ext.append(f"<{tag} {attr}={v[:80]}>")
        if tag == "link" and a.get("href") and EXTERNAL.match(a["href"]):
            self.ext.append(f"<link rel={a.get('rel')} href={a['href'][:80]}>")
        if tag in ("iframe", "embed", "object") and (a.get("src") or a.get("data")):
            self.ext.append(f"<{tag}> embeds content")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = Path(sys.argv[1])
    strict = "--strict" in sys.argv
    raw = path.read_bytes()
    html = raw.decode("utf-8", errors="replace")
    s = Scan()
    s.feed(html)
    s.has["title"] = bool(s.title.strip())

    fails, warns = [], []

    # Size
    kb = len(raw) / 1024
    if kb > 15 * 1024:
        fails.append(f"size {kb:.0f} KB > 15 MB")
    elif kb > 3 * 1024:
        warns.append(f"size {kb:.0f} KB > 3 MB (inline fewer/smaller images or libraries)")

    # Structure
    for k, v in s.has.items():
        if not v:
            fails.append(f"missing {k}")
    h1 = s.headings.count(1)
    if h1 != 1:
        warns.append(f"{h1} <h1> elements (want exactly 1)")
    for prev, cur in zip(s.headings, s.headings[1:]):
        if cur > prev + 1:
            warns.append(f"heading level skips h{prev} -> h{cur}")
            break
    dup = {i for i in s.ids if s.ids.count(i) > 1}
    if dup:
        fails.append(f"duplicate ids: {', '.join(sorted(dup))[:200]}")

    # Self-containment
    fails += [f"external resource: {e}" for e in s.ext]
    css_blocks = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    css_blocks += " ".join(re.findall(r'style="([^"]*)"', html))
    for m in re.finditer(r"@import\s+[^;]+;|url\(\s*['\"]?((?:https?:)?//[^'\")]+)", css_blocks, re.I):
        fails.append(f"external CSS: {m.group(0)[:80]}")
    # Vendored libraries (inlined by build_report.py) legitimately contain fetch/XHR code paths; only scan our own scripts.
    scripts = " ".join(re.findall(r"<script(?![^>]*(?:application/json|data-inlined))[^>]*>(.*?)</script>", html, re.S | re.I))
    for name in re.findall(r'<script\b[^>]*\bdata-vendor="([\w.-]+)"', html, re.I):
        fails.append(f"vendor placeholder not inlined: {name} (run scripts/build_report.py)")
    for pat, label in (
        (r"\bfetch\s*\(", "fetch()"),
        (r"XMLHttpRequest", "XMLHttpRequest"),
        (r"\bimport\s*\(", "dynamic import()"),
        (r"new\s+WebSocket", "WebSocket"),
        (r"\bnew\s+EventSource", "EventSource"),
    ):
        if re.search(pat, scripts):
            fails.append(f"network call in script: {label}")
    if re.search(r"fonts\.googleapis|fonts\.gstatic|use\.typekit", html, re.I):
        fails.append("web font service referenced")

    # Content hygiene (ignore inside <script> and <style>)
    body_text = re.sub(r"<(script|style|template)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    for pat, label in (
        (r"\{\{[^}]*\}\}", "unfilled {{placeholder}}"),
        (r"lorem ipsum", "lorem ipsum"),
        (r"\b(TODO|TBD|FIXME|XXX)\b", "TODO/TBD marker"),
    ):
        hits = re.findall(pat, body_text, re.I if "lorem" in pat else 0)
        if hits:
            fails.append(f"{label} x{len(hits)} (e.g. {str(hits[0])[:40]!r})")

    # Nice-to-haves
    if "prefers-color-scheme" not in html:
        fails.append("no dark-mode styles (prefers-color-scheme): Auto mode must follow the OS")
    if not re.search(r"data-theme-switch", html) or not all(re.search(r'data-mode="%s"' % m, html) for m in ("light", "auto", "dark")):
        fails.append("missing Light/Auto/Dark theme switch ([data-theme-switch] with data-mode light, auto, dark)")
    if not re.search(r':root\[data-theme="dark"\]', html) or 'not([data-theme="light"])' not in html:
        fails.append('theme CSS must define :root[data-theme="dark"] and @media dark :root:not([data-theme="light"])')
    if "@media print" not in html:
        warns.append("no print styles")
    viz = len(re.findall(r"<svg|<canvas|data-viz|THREE\.|d3\.", html_own := re.sub(r'<script[^>]*data-inlined[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)))
    if viz < 3:
        warns.append(f"only {viz} visual hooks (svg/canvas/d3/THREE): report may be too text-heavy")
    ctrls = len(re.findall(r'<input|<select|<button|data-tab=|data-node=', html_own, re.I))
    if ctrls < 6:
        warns.append(f"only {ctrls} interactive controls: add widgets the reader can manipulate")
    if "THREE." in html_own and not re.search(r"webgl", html_own, re.I):
        warns.append("three.js used without a WebGL-unavailable fallback")
    words = len(re.findall(r"\b\w+\b", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style|template|svg)[^>]*>.*?</\1>", " ", html_own, flags=re.S | re.I))))
    if words > 2500:
        warns.append(f"{words} words of visible text: cut prose, show it instead")
    if "<details" not in html and 'class="tabs"' not in html:
        warns.append("no progressive disclosure (details/tabs)")

    print(f"{path.name}: {kb:.0f} KB, title={s.title.strip()[:60]!r}")
    for f in fails:
        print(f"  FAIL  {f}")
    for w in warns:
        print(f"  warn  {w}")
    ok = not fails and not (strict and warns)
    print("  PASS" if ok else "  NOT OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
