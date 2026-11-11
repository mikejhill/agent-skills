# Final QA Checklist

Build with `python scripts/build_report.py src.html out.html`, then run `python scripts/check_report.py out.html`. The linter covers the ✱ items automatically.

## Content

- [ ] Headline answers "so what?" in one sentence.
- [ ] First screen shows headline, 3–5 KPIs, and the ask (or "FYI").
- [ ] Every number/claim traces to the work, a source, or is labelled *estimate*.
- [ ] No placeholder text (`lorem`, `TODO`, `TBD`, `XXX`, `{{…}}`). ✱
- [ ] Items referenced elsewhere are numbered (R1, Q2, Step 3) and anchor-linked.
- [ ] Risks and open questions are explicit, not buried.
- [ ] Prose blocks ≤ ~4 lines; anything longer became a list, table, or visual.

## Visual & interactive richness

- [ ] One clear signature interactive the reader can play with.
- [ ] ≥ 3 interactive visuals; every section leads with a visual or widget. ✱ (heuristic)
- [ ] ≥ 1 what-if control (slider/toggle → model/projection), defaulted to real current values.
- [ ] Views that share data are linked through one state object.
- [ ] Every mark has a tooltip; every chart title states the takeaway.
- [ ] Visible prose ≲ 1,500 words. ✱ (warns > 2,500)
- [ ] 3D is used only where space or structure carries meaning, has a side panel and controls, and its WebGL fallback works. ✱

## Self-containment ✱

- [ ] No `http(s)://` in `src`, `href` on `<link>`, `@import`, `url()`; no `fetch`/`XMLHttpRequest`/`import()`.
- [ ] Images are inline SVG or `data:` URIs.
- [ ] System font stack only.
- [ ] Libraries inlined via `build_report.py` (no leftover `data-vendor` placeholders).
- [ ] File size < 3 MB (warn), < 15 MB (fail).
- [ ] Outbound `<a href>` links to sources are fine — they're citations, not dependencies.

## Structure ✱

- [ ] `<!doctype html>`, `<html lang>`, `<meta charset>`, `<meta viewport>`, `<title>`.
- [ ] One `<h1>`; heading levels don't skip.
- [ ] `<main>` present; sections have ids for nav.

## Visual

- [ ] Looks right at 1280px and 390px wide; no horizontal scroll.
- [ ] Light / Auto / Dark switch present, Auto default; both themes legible; every chart/3D scene re-colours on switch and on OS change. ✱ (switch + CSS)
- [ ] Status never conveyed by color alone.
- [ ] Only one accent color; status colors used only for status.
- [ ] Tables scroll inside their own wrapper on mobile.

## Interaction

- [ ] All content reachable with JS disabled (tabs fall back to stacked panels).
- [ ] Every interactive control works with keyboard (Tab, Enter/Space) and touch.
- [ ] No console errors; no blank canvases (test headless with `--use-angle=swiftshader --enable-unsafe-swiftshader`).
- [ ] Render loops pause off-screen; reduced motion disables auto-rotate and animations.
- [ ] Print preview expands details and hides chrome.
