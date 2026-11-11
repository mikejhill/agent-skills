# d3 Recipes

Assume `<script data-vendor="d3"></script>` and the template's `R` runtime. Every chart follows the same skeleton so it is responsive and theme-aware:

```js
function drawX(){
  var el=d3.select('#v-x'); el.selectAll('*').remove();
  var W=el.node().clientWidth||600, H=280, m={t:16,r:16,b:32,l:48};
  var svg=el.append('svg').attr('viewBox',[0,0,W,H]).attr('width','100%')
    .attr('role','img').attr('aria-label','TAKEAWAY SENTENCE');
  // scales → axes (class "axis") → marks (colors from R.css) → labels → tooltips
}
drawX(); R.onTheme(drawX); addEventListener('resize', debounce(drawX,150));
```

Axes: `svg.append('g').attr('class','axis')…call(d3.axisBottom(x).ticks(5).tickSize(-innerH)).call(g=>g.select('.domain').remove())` gives gridlines in `--border`. Tooltips: `.on('mousemove',(e,d)=>R.tip.show(e,html)).on('mouseleave',R.tip.hide)`. Escape any data text with `R.esc`.

## Sorted horizontal bar (with direct labels)

```js
data.sort((a,b)=>b.v-a.v);
var x=d3.scaleLinear().domain([0,d3.max(data,d=>d.v)]).nice().range([m.l,W-m.r]);
var y=d3.scaleBand().domain(data.map(d=>d.k)).range([m.t,H-m.b]).padding(.25);
svg.selectAll('rect').data(data).join('rect').attr('x',m.l).attr('y',d=>y(d.k)).attr('height',y.bandwidth()).attr('rx',3)
  .attr('fill',R.css('--c1')).attr('width',0).transition().duration(R.reduced?0:600).attr('width',d=>x(d.v)-m.l);
svg.selectAll('text.v').data(data).join('text').attr('class','v').attr('x',d=>x(d.v)+6).attr('y',d=>y(d.k)+y.bandwidth()/2+4).attr('fill',R.css('--text')).text(d=>d.v);
```

## Line / area over time + brush to zoom (focus + context)

```js
var x=d3.scaleUtc().domain(d3.extent(data,d=>d.t)).range([m.l,W-m.r]);
var y=d3.scaleLinear().domain([0,d3.max(data,d=>d.v)]).nice().range([H-m.b,m.t]);
var line=d3.line().x(d=>x(d.t)).y(d=>y(d.v)).curve(d3.curveMonotoneX);
var path=svg.append('path').datum(data).attr('fill','none').attr('stroke',R.css('--c1')).attr('stroke-width',2).attr('d',line);
// threshold
svg.append('line').attr('x1',m.l).attr('x2',W-m.r).attr('y1',y(LIMIT)).attr('y2',y(LIMIT)).attr('stroke',R.css('--bad')).attr('stroke-dasharray','4 4');
// brush on a small context chart below sets S.range; main chart rescales x.domain(S.range) and transitions
var brush=d3.brushX().extent([[m.l,0],[W-m.r,40]]).on('brush end',e=>{ if(e.selection) S.set('range',e.selection.map(xCtx.invert)); });
// hover rule: d3.bisector(d=>d.t).center(data, x.invert(px)) → nearest point → R.tip
```

## Scatter + zoom/pan + hover

```js
var zoom=d3.zoom().scaleExtent([1,20]).on('zoom',e=>{ var zx=e.transform.rescaleX(x), zy=e.transform.rescaleY(y);
  dots.attr('cx',d=>zx(d.x)).attr('cy',d=>zy(d.y)); gx.call(d3.axisBottom(zx)); gy.call(d3.axisLeft(zy)); });
svg.call(zoom);
```

Use `<canvas>` instead of SVG above ~5,000 points.

## Unit / waffle chart (counts people can feel)

One square per item, coloured by outcome. Great for "17 of 46". See `examples/sample-report.src.html` → `drawBursts`.

## Force-directed graph (dependencies, relationships)

```js
var sim=d3.forceSimulation(nodes).force('link',d3.forceLink(links).id(d=>d.id).distance(50))
  .force('charge',d3.forceManyBody().strength(-180)).force('center',d3.forceCenter(W/2,H/2)).force('collide',d3.forceCollide(14));
// drag: d3.drag().on('start',e=>{if(!e.active)sim.alphaTarget(.3).restart();e.subject.fx=e.x;e.subject.fy=e.y})…
// focus: on click, fade nodes/links not adjacent to the clicked node (opacity .15), show detail in side panel
if(R.reduced){ sim.stop(); for(var i=0;i<300;i++) sim.tick(); render(); }
```

Add a search box that highlights and centres a node. Above ~300 nodes, consider a 3D force layout in three.js or aggregate.

## Zoomable treemap / partition (scope breakdown)

```js
var root=d3.hierarchy(tree).sum(d=>d.size).sort((a,b)=>b.value-a.value);
d3.treemap().size([W,H]).paddingInner(2).paddingTop(18).round(true)(root);
// click a group → re-run treemap on that subtree and transition rects; breadcrumb to go back up
```

Label only rects large enough (`w>60 && h>20`). Colour by top-level group (`--c1..--c6`) and use lightness for depth.

## Heatmap (time × category, matrix)

`d3.scaleBand` for both axes; `d3.scaleSequential(d3.interpolateRgb(R.css('--surface-2'), R.css('--c1')))`. Show a legend ramp with min/max labels. Clicking a cell filters linked views.

## Small multiples

Same scale across panels (shared `y.domain`) so comparisons are honest. Lay them out in a CSS grid (`repeat(auto-fit,minmax(220px,1fr))`) and draw each panel with the same function.

## Animating state changes

Use keyed joins (`.data(data, d=>d.id)`) and `.join(enter=>…, update=>…, exit=>…)` with transitions so items move rather than pop. Duration 300–700 ms, `0` when `R.reduced`.
