#!/usr/bin/env python3
"""Inline vendored libraries into a report so it ships as ONE self-contained file.

Usage:
  python build_report.py src.html out.html

In src.html, mark each library with an empty placeholder tag:
  <script data-vendor="three"></script>     -> assets/vendor/three.min.js   (global THREE, incl. THREE.OrbitControls)
  <script data-vendor="d3"></script>        -> assets/vendor/d3.min.js      (global d3)
  <script data-vendor="lil-gui"></script>   -> assets/vendor/lil-gui.min.js (global lil, use new lil.GUI())

Any other name resolves to assets/vendor/<name>.min.js or assets/vendor/<name>.js.
Each library is inlined once even if referenced twice. Stdlib only.
"""
import re
import sys
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "assets" / "vendor"
TAG = re.compile(r'<script\b[^>]*\bdata-vendor="([\w.-]+)"[^>]*>\s*</script>', re.I)


def resolve(name: str) -> Path:
    for cand in (VENDOR / f"{name}.min.js", VENDOR / f"{name}.js"):
        if cand.exists():
            return cand
    avail = ", ".join(sorted(p.name for p in VENDOR.glob("*.js")))
    sys.exit(f"build_report: unknown vendor '{name}'. Available: {avail}")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    html = src.read_text(encoding="utf-8")
    seen: set[str] = set()

    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name in seen:
            return f"<!-- vendor {name} already inlined -->"
        seen.add(name)
        code = resolve(name).read_text(encoding="utf-8")
        code = re.sub(r"</(script)", r"<\\/\1", code, flags=re.I)  # never close the tag early
        return f'<script data-inlined="{name}">\n{code}\n</script>'

    built = TAG.sub(repl, html)
    out.write_text(built, encoding="utf-8")
    kb = len(built.encode("utf-8")) / 1024
    print(f"built {out} ({kb:,.0f} KB) inlined: {', '.join(sorted(seen)) or 'none'}")


if __name__ == "__main__":
    main()
