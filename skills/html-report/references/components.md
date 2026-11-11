# Components

Static and lightly interactive building blocks. For charts see `d3-recipes.md`, for 3D see `three-recipes.md`, and for signature interactives see `interactive-patterns.md`. Prefer the d3 recipes over the hand-rolled SVG bar chart below whenever d3 is inlined.

Copy-paste snippets. All assume `assets/template.html` (tokens + CSS + helper script). Helpers are wired by `data-*` attributes — no per-component JS unless noted.

| Component | Use for | Helper |
|---|---|---|
| [KPI tile](#kpi-tile) | Top facts | — |
| [Ask card](#ask-card) | Decision needed | — |
| [Pills & callouts](#pills--callouts) | Status, warnings | — |
| [Tabs](#tabs) | Parallel views | `.tabs` |
| [Before/after switch](#beforeafter-switch) | Design changes | `.seg[data-target]` |
| [Diff block](#diff-block) | Code/config change | — |
| [Filterable, sortable table](#filterable-sortable-table) | Inventories | `data-filter`, `.chips`, `table.sortable` |
| [Accordion](#accordion) | Long detail | `details`, `data-expand-all` |
| [Timeline](#timeline) | Chronology | — |
| [Stepper + progress](#stepper--progress) | Plans | `data-progress` |
| [SVG diagram + detail panel](#svg-diagram--detail-panel) | Architecture, flow | `data-node` |
| [Bar chart from JSON](#bar-chart-from-json) | Magnitudes | small inline JS |
| [Sparkline](#sparkline) | Inline trend | — |
| [Gantt](#gantt) | Schedules | — |
| [Risk matrix](#risk-matrix) | Likelihood × impact | — |
| [Weighted scoring](#weighted-scoring) | Decisions | small inline JS |
| [Option cards](#option-cards) | Alternatives | — |
| [Citations](#citations) | Research | `:target` CSS |

---

## KPI tile

```html
<div class="kpis">
  <div class="kpi ok"><div class="label">Tests passing</div><div class="value">412</div><div class="delta">▲ 38 vs main</div></div>
  <div class="kpi warn"><div class="label">Open risks</div><div class="value">3</div><div class="delta muted">1 high</div></div>
</div>
```

Value = number or 1–2 words. Label ≤ 3 words. Delta gives the comparison that makes the number meaningful.

## Ask card

```html
<aside class="ask"><div class="label">Decision needed</div>
  <h3>Ship behind a flag or migrate all tenants at once?</h3>
  <p class="meta">Recommended: <strong>Flag (Option B)</strong> · by Fri 14 Nov</p></aside>
```

No decision? Use `<div class="label">For awareness</div>` and state what the reader should know/do.

## Pills & callouts

```html
<span class="pill ok">Done</span> <span class="pill warn">At risk</span> <span class="pill bad">Blocked</span> <span class="pill info">In review</span> <span class="pill plain">v2.4</span>
<div class="callout warn"><strong>Breaking change</strong>Clients on SDK &lt; 3.1 must upgrade before rollout.</div>
```

## Tabs

```html
<div class="tabs">
  <div class="tablist"><button data-tab="t-a">Option A</button><button data-tab="t-b" data-default>Option B ★</button></div>
  <div class="tab-panel" id="t-a"><h3>Option A</h3>…</div>
  <div class="tab-panel" id="t-b"><h3>Option B</h3>…</div>
</div>
```

Without JS the tablist hides and panels stack — so give each panel its own heading.

## Before/after switch

```html
<div class="seg" data-target="#cmp"><button data-view="before">Before</button><button data-view="after">After</button><button data-view="both">Side by side</button></div>
<div id="cmp" class="grid-2" style="margin-top:12px">
  <div class="card" data-show="before both"><h3>Before</h3>…</div>
  <div class="card" data-show="after both"><h3>After</h3>…</div>
</div>
```

## Diff block

```html
<style>.diff{font:13px/1.5 var(--mono);background:var(--surface-2);border-radius:8px;overflow:auto;padding:8px 0}
.diff div{padding:0 14px;white-space:pre}.diff .a{background:var(--ok-soft)}.diff .a::before{content:"+ ";color:var(--ok)}
.diff .r{background:var(--bad-soft)}.diff .r::before{content:"- ";color:var(--bad)}.diff .c::before{content:"  "}
.diff .h{color:var(--muted);padding-top:6px}</style>
<div class="diff" role="figure" aria-label="Diff of src/auth/session.ts">
  <div class="h">@@ src/auth/session.ts:42 @@</div>
  <div class="c">const ttl = config.session.ttl;</div>
  <div class="r">return sign(user, { expiresIn: ttl });</div>
  <div class="a">return sign(user, { expiresIn: ttl, audience: tenant.id });</div>
</div>
```

Show only the hunks that matter (≤ ~25 lines each). Escape `<`, `>`, `&`.

## Filterable, sortable table

```html
<div class="filter-bar">
  <input type="search" placeholder="Filter files…" data-filter="#files" aria-label="Filter">
  <div class="chips" data-filter-chips="#files" data-group="type">
    <button class="chip" data-value="*" aria-pressed="true">All</button>
    <button class="chip" data-value="add">Added</button><button class="chip" data-value="mod">Modified</button><button class="chip" data-value="del">Deleted</button>
  </div>
  <span class="meta" data-count="#files"></span>
</div>
<div class="table-wrap"><table class="sortable" id="files">
  <thead><tr><th>Path</th><th>Change</th><th class="num" data-type="num">Lines</th><th>Why</th></tr></thead>
  <tbody>
    <tr data-tags="mod"><td><code>src/auth/session.ts</code></td><td><span class="pill warn">mod</span></td><td class="num">+18 −4</td><td>Add audience claim</td></tr>
  </tbody></table><div class="empty-note">No matches.</div></div>
```

Multiple chip groups AND together; add `data-multi` to a group for OR-within-group multi-select. For card grids, put `data-item data-tags="…"` on each card and point `data-filter` at the grid container.

## Accordion

```html
<button class="icon-btn" data-expand-all="#faq" style="padding:0 10px">Expand all</button>
<div id="faq">
  <details><summary>Why not cache at the edge? <span class="pill plain">Q3</span></summary><div class="body">…</div></details>
</div>
```

Summary line must be informative on its own (state the conclusion, not just the topic).

## Timeline

```html
<ol class="timeline">
  <li class="ok"><strong>Mon 3 Nov</strong> · Spike merged <div class="meta">PR #812</div></li>
  <li class="now"><strong>Today</strong> · Migration dry-run</li>
  <li><strong>Fri 14 Nov</strong> · Rollout 10%</li>
</ol>
```

Classes: `ok` done, `now` current, `warn` slipping, `bad` missed, none = future.

## Stepper + progress

```html
<div style="display:flex;justify-content:space-between"><strong>Plan</strong><span class="meta" data-progress-label="#p1"></span></div>
<div class="bar ok" id="p1"><span></span></div>
<ol class="stack" style="padding-left:1.2em">
  <li><label><input type="checkbox" id="s1" data-progress="#p1"> <strong>Add audience claim</strong> — session.ts, 1h</label></li>
  <li><label><input type="checkbox" id="s2" data-progress="#p1"> <strong>Backfill tokens</strong> — migration 0042, 2h</label></li>
</ol>
```

Checkbox state persists per viewer in localStorage (convenience only). Pre-check finished steps with `checked`.

## SVG diagram + detail panel

```html
<div class="grid-2">
<svg class="diagram" viewBox="0 0 560 220" role="img" aria-labelledby="dg-t">
  <title id="dg-t">Request flow: Client → Gateway → Auth (changed) → Sessions DB</title>
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrow" d="M0,0L10,5L0,10z"/></marker></defs>
  <g class="node" data-node="client"><rect x="10" y="80" width="110" height="56" rx="8"/><text x="65" y="113" text-anchor="middle">Client</text></g>
  <g class="node changed" data-node="auth"><rect x="220" y="80" width="120" height="56" rx="8"/><text x="280" y="106" text-anchor="middle">Auth svc</text><text class="sub" x="280" y="124" text-anchor="middle">changed</text></g>
  <g class="node new" data-node="db"><rect x="430" y="80" width="120" height="56" rx="8"/><text x="490" y="113" text-anchor="middle">Sessions DB</text></g>
  <path class="edge" d="M120,108H218" marker-end="url(#ah)"/><path class="edge new" d="M340,108H428" marker-end="url(#ah)"/>
</svg>
<div class="card tight" data-node-panel><p class="muted">Click a box for details.</p></div>
</div>
<template id="node-auth"><h3>Auth service</h3><p>Adds <code>aud</code> claim; validates per tenant.</p></template>
<template id="node-client"><h3>Client</h3><p>No change.</p></template>
<template id="node-db"><h3>Sessions DB</h3><p>New table <code>session_audience</code>.</p></template>
<div class="legend"><span><i style="border-color:var(--ok)"></i>New</span><span><i style="border-color:var(--warn)"></i>Changed</span><span><i style="border-color:var(--bad);border-style:dashed"></i>Removed</span></div>
```

Layout tips: lay nodes on a grid (columns every ~200 units); keep ≤ 9 nodes per diagram (split otherwise); route edges orthogonally (`H`/`V` path commands); label edges with small `.sub` text at midpoints. Give complex diagrams a `<details>` text fallback.

## Bar chart from JSON

```html
<div id="chart-effort"></div>
<script type="application/json" id="data-effort">[{"k":"Backend","v":34},{"k":"Frontend","v":21},{"k":"Migration","v":12},{"k":"Docs","v":4}]</script>
<script>
(function(){ /* horizontal bars, sorted desc, direct labels */
  var data=JSON.parse(document.getElementById('data-effort').textContent).sort(function(a,b){return b.v-a.v});
  var max=Math.max.apply(null,data.map(function(d){return d.v})), rowH=30, W=600, L=110, R=50, H=data.length*rowH+10;
  var s='<svg class="diagram" viewBox="0 0 '+W+' '+H+'" role="img" aria-label="Effort by area (hours)">';
  data.forEach(function(d,i){var y=i*rowH+5, w=(W-L-R)*d.v/max;
    s+='<text x="'+(L-8)+'" y="'+(y+17)+'" text-anchor="end">'+d.k+'</text>'+
       '<rect x="'+L+'" y="'+(y+4)+'" width="'+w+'" height="'+(rowH-10)+'" rx="4" fill="var(--c1)"><title>'+d.k+': '+d.v+'</title></rect>'+
       '<text x="'+(L+w+6)+'" y="'+(y+17)+'" class="sub">'+d.v+'</text>';});
  document.getElementById('chart-effort').innerHTML=s+'</svg>';
})();
</script>
<noscript><!-- static table fallback --></noscript>
```

Chart rules: sort bars; start axis at 0; direct-label values; ≤ 6 colors; title states the takeaway ("Backend is half the effort"), not just the metric.

## Sparkline

```html
<svg viewBox="0 0 100 24" width="100" height="24" role="img" aria-label="p95 latency, 14 days, trending down">
  <polyline fill="none" stroke="var(--accent)" stroke-width="2" points="0,6 8,8 16,5 24,9 32,10 40,12 48,11 56,14 64,15 72,16 80,18 88,17 100,19"/>
</svg>
```

Y is inverted (0 = top). Normalize values to 2–22.

## Gantt

```html
<style>.gantt{display:grid;grid-template-columns:140px 1fr;gap:6px 12px;align-items:center;font-size:.9rem}
.gantt .track{position:relative;height:22px;background:var(--surface-2);border-radius:6px}
.gantt .seg-bar{position:absolute;top:0;bottom:0;border-radius:6px;background:var(--accent);color:#fff;font-size:.75rem;padding:0 8px;display:flex;align-items:center;white-space:nowrap;overflow:hidden}
.gantt .scale{display:flex;justify-content:space-between;color:var(--muted);font-size:.75rem}</style>
<div class="gantt">
  <span></span><div class="scale"><span>W1</span><span>W2</span><span>W3</span><span>W4</span></div>
  <span>Design</span><div class="track"><div class="seg-bar" style="left:0;width:25%;background:var(--ok)" title="Done">done</div></div>
  <span>Build</span><div class="track"><div class="seg-bar" style="left:20%;width:50%">Build</div></div>
  <span>Rollout</span><div class="track"><div class="seg-bar" style="left:70%;width:30%;background:var(--c4)">Rollout</div></div>
</div>
```

## Risk matrix

```html
<style>.rm{display:grid;grid-template-columns:auto repeat(3,1fr);gap:4px;font-size:.85rem}
.rm .cell{min-height:64px;border-radius:6px;padding:6px;display:flex;flex-wrap:wrap;gap:4px;align-content:flex-start}
.rm .lo{background:var(--ok-soft)}.rm .md{background:var(--warn-soft)}.rm .hi{background:var(--bad-soft)}
.rm .ax{color:var(--muted);display:flex;align-items:center;justify-content:center;font-size:.75rem}
.rm a{font-weight:700;text-decoration:none;background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:1px 8px}</style>
<div class="rm" role="table" aria-label="Risk matrix: likelihood (rows) by impact (columns)">
  <div class="ax">High</div><div class="cell md"></div><div class="cell hi"><a href="#r2">R2</a></div><div class="cell hi"></div>
  <div class="ax">Med</div><div class="cell lo"></div><div class="cell md"><a href="#r1">R1</a></div><div class="cell hi"></div>
  <div class="ax">Low</div><div class="cell lo"><a href="#r3">R3</a></div><div class="cell lo"></div><div class="cell md"></div>
  <div></div><div class="ax">Low impact</div><div class="ax">Med</div><div class="ax">High</div>
</div>
```

Each `R#` links to a risk card (`id="r1"`) with mitigation + owner.

## Weighted scoring

```html
<div class="table-wrap"><table id="score">
  <thead><tr><th>Criterion</th><th>Weight</th><th class="num">A</th><th class="num">B</th><th class="num">C</th></tr></thead>
  <tbody>
    <tr><td>Effort</td><td><input type="range" min="0" max="5" value="3" aria-label="Weight: effort"></td><td class="num">4</td><td class="num">3</td><td class="num">1</td></tr>
    <tr><td>Risk</td><td><input type="range" min="0" max="5" value="4" aria-label="Weight: risk"></td><td class="num">2</td><td class="num">4</td><td class="num">5</td></tr>
  </tbody>
  <tfoot><tr><th>Total</th><th></th><th class="num" data-total="2"></th><th class="num" data-total="3"></th><th class="num" data-total="4"></th></tr></tfoot>
</table></div>
<script>
(function(){var t=document.getElementById('score');function calc(){var tot={},best=-1,bi;
  t.querySelectorAll('tbody tr').forEach(function(r){var w=+r.querySelector('input').value;for(var c=2;c<r.cells.length;c++)tot[c]=(tot[c]||0)+w*(+r.cells[c].textContent)});
  t.querySelectorAll('[data-total]').forEach(function(th){var v=tot[th.dataset.total];th.textContent=v;th.style.color='';if(v>best){best=v;bi=th}});if(bi)bi.style.color='var(--ok)';}
  t.addEventListener('input',calc);calc();})();
</script>
```

Scores: higher = better on every row (invert cost-type criteria). Say the scale (1–5) above the table.

## Option cards

```html
<div class="grid">
  <div class="card"><span class="pill plain">A</span><h3>Big-bang migration</h3><p class="meta">2 days · irreversible</p>
    <ul><li class="add">✓ Simplest code</li><li class="del">✕ Full outage risk</li></ul></div>
  <div class="card" style="border-color:var(--accent)"><span class="pill accent">B · Recommended</span><h3>Feature flag</h3>…</div>
</div>
```

## Citations

```html
<style>.cite:target{background:var(--accent-soft);border-radius:6px}</style>
<p>Cold starts dropped 40% after the switch <a href="#src-2">[2]</a>.</p>
<ol><li id="src-2" class="cite"><a href="https://example.com/bench">Benchmark run 2026-11-02</a> — internal, n=500</li></ol>
```
