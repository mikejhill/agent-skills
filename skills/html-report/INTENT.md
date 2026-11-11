# Intent

Teach any agent to produce single-file, self-contained, interactive HTML reports
that communicate a topic (design changes, scope, plans, research, decisions,
incidents, status) faster than prose.

## Goals

1. Answer first: headline, key facts, and the decision needed on the first screen.
2. Explorable, not readable: a signature interactive (what-if model, 3D system, live demo, linked views) plus d3 charts and widgets; prose is captions.
3. Progressive disclosure: summary visible, depth behind tabs/accordions/panels.
4. Zero network dependencies: d3, three.js and lil-gui are vendored and inlined by build_report.py, so reports share via email, chat, or disk.
5. Agent-agnostic: plain Markdown, relative paths, stdlib-only Python linter.
6. Real content only: no placeholders or invented metrics.
7. Standard Light / Auto / Dark theme switch on every report; Auto (follow OS) is the default.

## Log

- 2026-11-08: [agent] Created skill: SKILL.md, references (recipes, components,
  design system, checklist), base template, check_report.py linter, sample report.
- 2026-11-08: [agent] v2 per user: reports must be truly interactive sites. Vendored d3 7.9.2,
  three r187 (+OrbitControls, IIFE bundle), lil-gui 0.21; added build_report.py, R runtime in
  template, interactive-patterns/d3-recipes/three-recipes references, richness checks in the linter,
  and a new sample (3D pipeline, live chunking demo, linked what-if).
- 2026-11-08: [agent] Standard Light/Auto/Dark switch (Auto default, pre-paint, persisted, R.theme API); linter enforces it.
