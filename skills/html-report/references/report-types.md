# Report Recipes

Pick the closest recipe. Mix sections when a topic spans types. Every recipe starts with the same **hero** (status pill + headline + one-line context + KPI tiles + ask card + a hero visual), then a **signature interactive** (see `interactive-patterns.md`). The tables below list supporting sections.

## 1. Design change (UI, API, architecture)

**Signature:** explorable system (3D or SVG) with a Before/After toggle that animates what moves; impact counters update live.

| Section | Visual | Interaction |
|---|---|---|
| What changes & why | 3-bullet summary + impact KPIs (files, endpoints, users affected) | — |
| Before → After | Side-by-side mock/diagram or code diff | Toggle "before / after / diff" |
| Architecture | SVG box-and-arrow diagram, changed nodes highlighted (`--warn`), new (`--ok`), removed (`--bad`, dashed) | Click node → detail panel |
| Impact matrix | Table: component × (behavior, perf, security, migration) with ✓/⚠/✕ | Filter by severity |
| Alternatives considered | Option cards with pros/cons + why rejected | Tabs |
| Rollout & rollback | Step timeline | — |

## 2. Project scope

**Signature:** zoomable treemap of the work breakdown (size = effort) linked to a scrubbable timeline.

| Section | Visual | Interaction |
|---|---|---|
| In / Out of scope | Two-column list, out-of-scope muted with ✕ | — |
| Work breakdown | Tree or nested cards (epic → task) with size chips (S/M/L) | Expand/collapse, expand-all |
| Effort distribution | Horizontal bar chart by area | Hover values |
| Timeline | Gantt/phase bar | Hover detail |
| Dependencies | Graph or table of blockers | Click to highlight chain |
| Risks | Likelihood × impact grid | Click cell → list |

## 3. Implementation plan (code work)

**Signature:** an interactive code map (force graph or 3D city of touched files, height = lines changed). Click a file to see its diff and purpose; the stepper highlights the files each step touches.

| Section | Visual | Interaction |
|---|---|---|
| Steps | Numbered stepper with status per step | Checkboxes (local only), progress bar |
| Files touched | Filterable table: path · change type (add/mod/del pill) · lines · purpose | Filter, sort |
| Key code | Short snippets with annotations | Copy button, tabs per file |
| Data/control flow | Sequence or flow SVG | — |
| Test plan | Table: case · type · expected | Filter by type |
| Open questions | Numbered Q-cards with owner | — |

## 4. Research / investigation

**Signature:** linked views. Brush or filter the evidence, and the charts and verdict confidence update. Include a live demo if the finding is a mechanism.

| Section | Visual | Interaction |
|---|---|---|
| Answer | Verdict + confidence meter (low/med/high) | — |
| Evidence | Finding cards each with source link + strength | Filter by theme/strength |
| Comparison | Feature matrix of options | Sort, highlight best per row |
| Data | Charts from embedded JSON | Toggle series |
| Unknowns | List of what wasn't verified & how to verify | — |
| Sources | Numbered citations; claims link `[n]` to them | Anchor + `:target` highlight |

## 5. Decision / trade-off

**Signature:** weighted decision lab with sliders, live re-ranking and a "what flips it" sensitivity readout.

| Section | Visual | Interaction |
|---|---|---|
| Decision needed | Big ask card: question, deadline, recommended option | — |
| Options | Cards side by side, recommended badged | — |
| Scoring | Weighted criteria table | Sliders adjust weights → totals re-rank live |
| Consequences | For each option: what happens next, cost, reversibility | Tabs |

## 6. Incident / postmortem

**Signature:** scrubbable incident timeline synced with metric charts (error rate, latency) and a system diagram that lights up affected components at the scrubbed time.

| Section | Visual | Interaction |
|---|---|---|
| Impact | KPIs: duration, users, errors, SLO burn | — |
| Timeline | Vertical timeline, color by phase (detect/mitigate/resolve) | Filter by phase |
| Root cause | Causal chain diagram (5 whys / fishbone) | — |
| Action items | Table: item · owner · priority · status | Sort/filter |

## 7. Status / progress

**Signature:** burn-up with forecast cone. Drag scope or velocity to see how the date moves.

| Section | Visual | Interaction |
|---|---|---|
| Health | RAG pills per workstream | — |
| Progress | Progress bars, burn-up line | — |
| Changes since last | Delta list (▲▼) | — |
| Blockers | Red cards, owner + needed-by | — |

## Picking a main visual by content shape

| Shape | Best visual |
|---|---|
| Comparison (A vs B vs C) | Matrix table or option cards |
| Sequence (steps, time) | Timeline, stepper, Gantt |
| Hierarchy (breakdown) | Tree / nested cards / treemap |
| Flow (data, requests, process) | Box-and-arrow or sequence diagram |
| Change | Before/after, diff |
| Distribution / magnitude | Bar chart (sorted), never pie > 4 slices |
| Trend | Line / sparkline |
| Inventory (many items) | Filterable, sortable table |
| Two-axis assessment | 2×2 or heat grid (risk, effort×value) |
| Spatial / layered system | three.js scene + side panel |
| Relationships | Force graph (d3) with focus-on-click |
| Mechanism | Live demo running the real logic |
