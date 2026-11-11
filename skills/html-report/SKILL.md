---
name: html-report
description: Build a single-file, self-contained, interactive HTML site that lets the reader explore a topic visually (charts, live widgets, simulations, 3D scenes) instead of reading about it. Use for design changes, project scope, implementation plans, research, decisions, incidents, status, explainers, or any "illustrate / show me / make a report" request, and whenever the work has structure (options, phases, data, systems, trade-offs) that a reader would grasp faster by manipulating it.
---

# Interactive HTML Report

Ship **one `.html` file** that works like a small interactive site. Within ten seconds the reader knows the verdict. Within two minutes, by dragging, toggling, hovering and orbiting, they understand the topic well enough to argue about it.

## The bar

| A report fails if… | It succeeds when… |
|---|---|
| It's a document with CSS | It's an **instrument**: the reader changes inputs and sees consequences |
| Charts are pictures | Charts are **linked**: hover shows detail, clicks filter other views |
| Concepts are explained in paragraphs | Concepts are **shown running** (simulation, live demo, animated flow) |
| Structure is described | Structure is **spatial**: diagram or 3D scene you can explore and click |
| Scrolling past text | Scrolling past **visuals**; text is captions, labels, tooltips |

**Minimum per report:** a hero answer (verdict, KPIs, ask) + **one signature interactive** (the centrepiece the reader plays with) + **≥ 3 interactive visuals** + **≥ 1 what-if control** (slider/toggle driving a model or projection) + linked views where data overlaps.

## Non-negotiables

1. **One file, zero network.** Libraries are inlined by `scripts/build_report.py` from `assets/vendor/`. No CDNs, no `fetch`, no web fonts. Opens from disk, email, chat.
2. **Answer first.** The first screen gives the headline, 3–5 KPIs, the decision needed, and a visual.
3. **Show, don't tell.** Every section leads with a visual or widget. Prose is at most 2 lines per block. Visible text stays under ~1,500 words.
4. **Real content only.** Numbers come from the work. Estimates, schematic layouts and illustrative demos are **labelled as such**. Never invent data to make a chart look full; pick a different visual.
5. **Light / Auto / Dark theme switch, Auto by default.** Every report keeps the template's three-way switch (`[data-theme-switch]`). Auto follows the OS live. Light and Dark override it and persist. Every chart and scene re-colours on change via `R.onTheme`. Don't remove the switch or hard-code colours. Standard implementation: `references/design-system.md` → *Theme*.
6. **Degrades, never breaks.** No WebGL means a fallback note plus 2D. No JS means the content and tables are still readable. 360px to desktop, `prefers-reduced-motion` respected.

## Toolkit (inlined, offline)

| Library | Global | Use for | Size |
|---|---|---|---|
| none (SVG/CSS/Canvas) | none | KPI tiles, timelines, simple bars, diagrams | 0 |
| **d3** v7 | `d3` | Any data chart, scales/axes, transitions, brushing, zoom, force graphs, treemaps, hierarchies, geo | 275 KB |
| **three.js** r187 + OrbitControls | `THREE`, `THREE.OrbitControls` | Spatial/structural topics: architectures, pipelines, layered systems, 3D data (x·y·z), physical things, large point clouds | 750 KB |
| **lil-gui** | `lil.GUI` | Compact parameter panel for simulations and 3D scenes | 29 KB |

Include only what you use. A d3-only report is about 330 KB, and everything together is about 1.1 MB. Use three.js when depth or space carries meaning or makes the subject vivid and explorable, **not** as decoration on a 2D chart.

## Workflow

1. **Distill:** headline, 3–5 facts, the ask, and the content **shape** (comparison, sequence, hierarchy, flow/system, change, distribution, trend, spatial, model/mechanism).
2. **Choose the signature interactive** (see `references/interactive-patterns.md`): the one experience that makes the topic click. Examples: a what-if model with sliders, a 3D system you orbit and click, a live algorithm demo, a scrubbable timeline, linked brushing across charts.
3. **Pick the rest:** recipe per report type in `references/report-types.md`. d3 charts in `references/d3-recipes.md`, 3D in `references/three-recipes.md`, static components in `references/components.md`.
4. **Write `report.src.html`** from `assets/template.html`. Keep the `<script data-vendor="…">` placeholders you need. Page code goes in the last `<script>`, after the helpers. Use the `R` runtime for tokens, theme changes, tooltips, the WebGL check, visibility and escaping.
5. **Build:** `python scripts/build_report.py report.src.html report.html`
6. **Verify:** `python scripts/check_report.py report.html`. Then, if any headless browser is available, load the page at 1280px and 390px in light and dark. Check for console errors, horizontal scroll, and blank canvases, and click every control once. Look at the screenshots and fix what's clipped, empty, cramped or unreadable.
7. **Deliver** the built file path plus a 1–3 line summary. Keep `.src.html` beside it for edits. Never paste HTML into chat.

## Design rules for visuals

- **Encode, then decorate.** Position/length > colour > size > shape. Sort bars. Start at zero. Label values directly; avoid legends where labels fit.
- **Colour has meaning.** One accent; status colours (`--ok/--warn/--bad/--info`) only for status; series `--c1..--c6`. Read tokens at draw time (`R.css('--c1')`) and redraw on `R.onTheme`.
- **Every mark answers a hover.** Tooltips (`R.tip`) give exact value + meaning. Clickable things look clickable (cursor, hover state) and have a keyboard path.
- **Linked state, single source.** Keep one shared state object; views subscribe and redraw (pattern in `interactive-patterns.md`). A toggle in the 3D scene and its twin in a chart stay in sync.
- **Motion explains, never decorates.** Animate transitions between states and flows through systems. No idle spinning unless it aids depth perception. Auto-rotate off under reduced motion. Pause render loops off-screen (`R.visible`).
- **Titles state the takeaway** ("Every alert happened during a backup run"), not the metric ("Alerts by context").
- **Schematic ≠ data.** If a 3D/diagram layout isn't to scale, say so in a hint.

## Layout skeleton

```
Sticky bar: title · section links · Light|Auto|Dark
HERO  status · headline · lede · KPIs | ask card · hero visual(s)
SIGNATURE INTERACTIVE  (stage .tall + side panel with controls/details)
Supporting explorables (viz-grid: chart + controls/panel)
What-if / decision (sliders → projected outcome, labelled estimate)
Plan / risks / open questions (timeline, risk grid, accordions)
Appendix: sources, assumptions, method
```

## Files

- `assets/template.html`: tokens, light/dark, components CSS, viz CSS (`.stage`, `.viz-grid`, `.control`, `.tip`), helpers (tabs, filters, sort, copy, expand) and the `R` runtime
- `assets/vendor/`: `d3.min.js`, `three.min.js`, `lil-gui.min.js` (license headers kept)
- `scripts/build_report.py`: inlines vendor placeholders into one file
- `scripts/check_report.py`: lints self-containment, structure, visual density, interactivity, WebGL fallback, placeholders
- `references/interactive-patterns.md`: signature interactives and linking patterns
- `references/d3-recipes.md`: chart recipes (bar, line+brush, scatter+zoom, force, treemap, heatmap, unit chart)
- `references/three-recipes.md`: scene boilerplate, picking, labels, instancing, 3D charts, camera tours
- `references/report-types.md`: recipes per report type
- `references/components.md`: static components (KPI, ask, tabs, diff, tables, timeline, risk grid…)
- `references/design-system.md`, `references/checklist.md`
- `examples/sample-report.html` (built) and `examples/sample-report.src.html` (source): 3D pipeline, live algorithm demo, linked what-if, d3 charts
