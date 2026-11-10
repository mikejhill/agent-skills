# three.js Recipes

Assume `<script data-vendor="three"></script>` (global `THREE`, includes `THREE.OrbitControls`) and the template's `R` runtime. Full working example: `examples/sample-report.src.html` → `pipeline()`.

## When 3D earns its place

Use it for layered systems and pipelines, physical or spatial subjects, three numeric dimensions, large node/point sets, and "walk around it" explanations. Don't use it for anything a 2D bar/line chart says better. Always pair the scene with a **side panel** (details on click) and **controls** (lil-gui or HTML).

## Scene boilerplate (theme-aware, responsive, pausable, with fallback)

```html
<div class="viz-grid">
  <div class="stage tall" id="scene" data-viz><div class="hint">Drag to orbit · scroll to zoom · click an object</div></div>
  <div class="panel" id="scene-panel" aria-live="polite"><h3>Click an object</h3>…static summary of the scene…</div>
</div>
```

```js
function scene3d(){
  var stage=document.getElementById('scene');
  if(!R.webgl()){ stage.insertAdjacentHTML('afterbegin','<div class="noscript-note"><strong>3D view needs WebGL.</strong> SUMMARY OF WHAT THE SCENE SHOWS</div>'); return; }
  var renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});         // alpha: page background shows through
  renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
  stage.prepend(renderer.domElement);
  var scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(40,1,0.1,500);
  var HOME=new THREE.Vector3(0,12,24); camera.position.copy(HOME);
  var controls=new THREE.OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true; controls.autoRotate=!R.reduced; controls.autoRotateSpeed=.5;
  scene.add(new THREE.HemisphereLight(0xffffff,0x667788,1.6));
  var sun=new THREE.DirectionalLight(0xffffff,1.6); sun.position.set(6,14,8); scene.add(sun);

  var col=function(t){ return new THREE.Color(R.css(t)); };                  // tokens → colours
  var mat=new THREE.MeshStandardMaterial({roughness:.6});
  function paint(){ mat.color=col('--c1'); /* …re-colour every material… */ }
  paint(); R.onTheme(paint);

  function resize(){ var w=stage.clientWidth,h=stage.clientHeight; renderer.setSize(w,h,false); camera.aspect=w/h;
    var k=Math.max(1,1.2/camera.aspect); camera.position.copy(HOME).multiplyScalar(k); camera.updateProjectionMatrix(); } // back off on narrow screens
  new ResizeObserver(resize).observe(stage); resize();

  var running=true; R.visible(stage,function(v){ running=v; if(v) requestAnimationFrame(loop); });   // pause off-screen
  function loop(){ if(!running) return; controls.update(); renderer.render(scene,camera); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);
}
try{ scene3d(); }catch(e){ console.error(e); }
```

## Click picking → side panel

```js
var ray=new THREE.Raycaster(), ptr=new THREE.Vector2(), down=null;
renderer.domElement.addEventListener('pointerdown',e=>{ down=[e.clientX,e.clientY]; });
renderer.domElement.addEventListener('pointerup',e=>{
  if(!down || Math.hypot(e.clientX-down[0],e.clientY-down[1])>5) return;      // ignore drags (orbit)
  var r=renderer.domElement.getBoundingClientRect();
  ptr.set((e.clientX-r.left)/r.width*2-1, -(e.clientY-r.top)/r.height*2+1); ray.setFromCamera(ptr,camera);
  var hit=ray.intersectObjects(scene.children,true).find(h=>h.object.userData.id);
  if(hit) select(hit.object.userData.id);                                       // fill panel from <template id="detail-ID">
});
```

Hover: same raycast on `pointermove` (throttled) → `R.tip.show(e, …)` + `renderer.domElement.style.cursor='pointer'`. For an `InstancedMesh`, `hit.instanceId` gives the item.

## HTML labels pinned to 3D points

Crisper than sprite text and theme-aware. Use the template's `.label3d` class.

```js
var labels=items.map(it=>{ var el=document.createElement('div'); el.className='label3d'; el.textContent=it.name; stage.appendChild(el); return {el, p:new THREE.Vector3(it.x,it.y+1.5,it.z)}; });
var v=new THREE.Vector3();
// in loop:
labels.forEach(l=>{ v.copy(l.p).project(camera); l.el.style.left=((v.x+1)/2*stage.clientWidth)+'px';
  l.el.style.top=((1-v.y)/2*stage.clientHeight)+'px'; l.el.style.display=v.z<1?'':'none'; });
```

Keep it to ≤ 15 labels. Show more only on hover or selection.

## Many objects: InstancedMesh

```js
var mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshStandardMaterial(), N), o=new THREE.Object3D();
for(var i=0;i<N;i++){ o.position.set(x[i],h[i]/2,z[i]); o.scale.set(.8,h[i],.8); o.updateMatrix(); mesh.setMatrixAt(i,o.matrix); mesh.setColorAt(i,col(i<K?'--c2':'--c1')); }
mesh.instanceMatrix.needsUpdate=true; mesh.instanceColor.needsUpdate=true; scene.add(mesh);
```

Use this for 3D bar charts and city-block views of files, services or regions (height = metric, colour = category). Thousands of instances stay fast.

## Flows: particles along paths

`THREE.Points` with a `Float32Array` position buffer, where each particle has `t∈[0,1]` along a `THREE.CatmullRomCurve3` or a lerp between stages. Advance `t` per frame and set `geometry.attributes.position.needsUpdate=true`. The particle rate and colour encode volume and type. Toggling a scenario changes the spawn rules, so the reader sees the flow change.

## 3D data plots

- **Scatter 3D:** `THREE.Points` with per-vertex colour, plus axes from `THREE.Line` and HTML tick labels. Add a lil-gui to pick which fields map to x/y/z.
- **Surface:** `PlaneGeometry(w,h,nx,ny)` and set each vertex `z=f(x,y)`, then `computeVertexNormals()`. Use a colour ramp via vertex colours and a wireframe overlay at low opacity.
- **Layered architecture:** stacked translucent slabs (one per layer) with components as boxes on top and edges as `Line`s between them. Clicking a slab isolates that layer by fading the others to opacity .15.

## Camera tour (guided presets)

```js
var stops=[{pos:[0,12,24],target:[0,0,0],caption:'Overview'},{pos:[-9,5,8],target:[-9,0,0],caption:'Walk stage'}];
function go(i){ var s=stops[i], p0=camera.position.clone(), t0=controls.target.clone(), p1=new THREE.Vector3(...s.pos), t1=new THREE.Vector3(...s.target), k=0;
  controls.autoRotate=false; (function step(){ k=Math.min(1,k+(R.reduced?1:.04)); var e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
    camera.position.lerpVectors(p0,p1,e); controls.target.lerpVectors(t0,t1,e); if(k<1) requestAnimationFrame(step); })(); caption.textContent=s.caption; }
```

Render the stops as numbered buttons over the stage (`.overlay`).

## lil-gui panel

```js
var gui=new lil.GUI({container:stage,title:'Controls',width:210});
var params={scenario:false,speed:1,rotate:controls.autoRotate,reset:()=>{camera.position.copy(HOME);controls.target.set(0,0,0);}};
gui.add(params,'scenario').name('Apply change').onChange(v=>S.set('scenario',v));   // write to shared state
gui.add(params,'speed',0,3,.1).name('Flow speed'); gui.add(params,'rotate').name('Auto-rotate').onChange(v=>controls.autoRotate=v);
gui.add(params,'reset').name('Reset camera'); if(stage.clientWidth<520) gui.close();
```

The template themes lil-gui with the page tokens and pins it to the top right of `.stage`. When shared state changes elsewhere, call `controller.updateDisplay()`.

## Pitfalls

- Don't load models, textures or HDRs from URLs. Build geometry procedurally or use small `data:` textures.
- Cap the pixel ratio at 2, and pause the loop off-screen.
- Keep the 3D layout honest. If it's schematic, say so in `.hint`.
- Give mobile a farther camera (see `resize`) and close the GUI below 520px.
- Headless test browsers may lack a GPU, so launch Chromium with `--use-angle=swiftshader --enable-unsafe-swiftshader` to verify.
