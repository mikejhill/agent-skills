# Interactive Patterns

Pick **one signature interactive** per report: the thing the reader plays with that makes the topic click. Add supporting explorables around it.

## Choosing the signature interactive

| Topic shape | Signature interactive | Typical tech |
|---|---|---|
| System / architecture / pipeline | **Explorable system**: orbit a 3D (or 2D) model, click components for detail, toggle a change on/off to see what moves | three.js or SVG + side panel |
| Design change | **Before/after scrubber**: drag a divider or toggle; changed parts highlight; impact counters update | SVG/HTML + d3 transitions |
| Trade-off / decision | **Weighted decision lab**: sliders for criteria weights → live re-ranking, sensitivity ("what weight flips the winner?") | d3 bars + range inputs |
| Plan / scope | **Scrubbable timeline**: drag a "today" handle; phases, risks and burn-up update; click a phase for its tasks | d3 time scale + brush |
| Mechanism / algorithm | **Live demo**: run the real algorithm on editable input; show intermediate state | vanilla JS + d3/Canvas |
| Research / data | **Linked views**: brush one chart, others filter; detail table follows | d3 brush + shared state |
| Performance / capacity | **What-if model**: sliders for load/params → projected latency/cost curve with a threshold line | d3 line + model fn |
| Spatial / physical | **3D scene** with presets (camera tour stops) and annotations | three.js |
| Hierarchy / scope breakdown | **Zoomable treemap/sunburst** with breadcrumb | d3.hierarchy + transitions |
| Dependencies / relationships | **Force graph** with search, focus-on-click (fade non-neighbours), drag | d3.forceSimulation (2D) or three (3D, >300 nodes) |

## Pattern: shared state + linked views

One source of truth; every view subscribes. Prevents drift between controls.

```js
var S={exclude:false, share:63, selected:null, subs:[]};
S.set=function(k,v){ if(S[k]===v) return; S[k]=v; S.subs.forEach(function(f){ f(k); }); };
S.on=function(f){ S.subs.push(f); };

// a control writes state
checkbox.addEventListener('change', function(){ S.set('exclude', checkbox.checked); });
// every view reads state when redrawing
S.on(function(k){ if(k==='exclude') checkbox.checked=S.exclude; drawChart(); update3D(); });
```

## Pattern: what-if model

```html
<div class="viz-grid">
  <div class="panel"><div id="v-model" data-viz></div></div>
  <div class="panel">
    <div class="control"><label for="m-load">Requests / s</label><output id="m-load-o"></output><input type="range" id="m-load" min="100" max="5000" step="100" value="1200"></div>
    <div class="kpis"><div class="kpi"><div class="label">p95 latency</div><div class="value" id="m-p95"></div></div></div>
    <div class="callout"><strong>Model</strong>M/M/c queue, c = 8, service 4 ms (measured). Estimate.</div>
  </div>
</div>
```

Rules: show the model's assumptions next to the controls. Mark the current/measured point on the curve. Draw a threshold line (SLO, budget). Default the sliders to today's real values.

## Pattern: live algorithm demo

Run the real logic in the page on editable or sample input. Show the intermediate state (boundaries, queue, tree), not just the result. Offer 2–3 one-click "experiments" (buttons) that demonstrate the key property, plus a reset. Compare against a naïve baseline side by side.

## Pattern: scroll-driven narrative (scrollytelling)

For explainers with an ordered argument. A sticky visual on one side and steps scrolling on the other; each step sets the state.

```html
<style>.scrolly{display:grid;grid-template-columns:1fr;gap:24px}@media(min-width:960px){.scrolly{grid-template-columns:1fr 1.3fr}}
.scrolly .sticky{position:sticky;top:72px;height:min(70vh,560px)} .step{min-height:60vh;opacity:.35;transition:opacity .2s}.step.on{opacity:1}</style>
<div class="scrolly"><div class="steps"><div class="step" data-step="0">…</div><div class="step" data-step="1">…</div></div><div class="sticky stage" id="sv"></div></div>
<script>
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){
  document.querySelectorAll('.step').forEach(function(s){s.classList.toggle('on',s===e.target)}); setStep(+e.target.dataset.step);}})},{rootMargin:'-45% 0px -45% 0px'});
document.querySelectorAll('.step').forEach(function(s){io.observe(s)});
</script>
```

On phones the sticky visual comes first, then the steps. Every step must also make sense as static text.

## Pattern: guided tour inside a visual

Buttons "1 · 2 · 3 · 4" that move the camera/zoom and highlight one element with a caption. Good for 3D scenes and big diagrams. The reader can leave the tour at any time and explore freely.

## Pattern: drill-down

Overview → click → detail in the side panel (not a modal) → breadcrumb back. Keep the overview visible. Use `<template id="detail-x">` blocks so detail content exists in the HTML (readable without JS, searchable).

## Pattern: compare by toggling

Segmented control `Before | After | Diff`. Animate between states with d3 transitions (positions interpolate) so the reader sees *what moved*. Counters for added/changed/removed update with the toggle.

## Interaction hygiene

- Every control shows its current value (`<output>`). Sliders default to the real/current value.
- Feedback within 100 ms; debounce heavy redraws (`resize`, text input).
- Hover and click both work; keyboard path for primary actions (buttons, inputs, `tabindex` + Enter on clickable SVG).
- Don't hide primary information behind hover only. Tooltips add precision; labels carry the message.
- Provide reset buttons for stateful explorables.
- Persist nothing important in `localStorage`. A reload restores the defaults.
