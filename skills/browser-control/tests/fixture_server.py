"""Fixture SPA for smoke_test.py: shadow-DOM custom elements, hash routing, timer and fetch delays."""
import http.server, json, time, sys
PAGE = r"""<!doctype html><html><head><title>Fixture SPA</title></head><body>
<app-shell></app-shell>
<script>
const sleep = ms => new Promise(r => setTimeout(r, ms));
class Card extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:'open'}); }
  set html(h){ this.shadowRoot.innerHTML = h; }
}
customElements.define('x-card', Card);
class Shell extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:'open'}); }
  connectedCallback(){ window.addEventListener('hashchange', () => this.route()); this.route(); }
  async route(){
    const r = location.hash.slice(1) || 'home';
    this.shadowRoot.innerHTML = '<nav><a href="#home">Home</a> | Help |</nav><main>Loading...</main>';
    const main = this.shadowRoot.querySelector('main');
    await sleep(300 + Math.random()*900);
    if (r === 'home') {
      main.innerHTML = '<h1>Welcome</h1><x-card id=c1></x-card>';
      main.querySelector('#c1').html = '<p>The catalog is open.</p><button id=browse>Browse</button>';
      main.querySelector('#c1').shadowRoot.querySelector('#browse').onclick = () => location.hash = 'items';
    } else if (r === 'items') {
      const d = await (await fetch('/api/items')).json();
      main.innerHTML = '<h1>Choose a Product</h1>';
      for (const p of d.items) {
        const c = document.createElement('x-card'); main.appendChild(c);
        c.html = `<h2>${p.name}</h2><span>Price</span> <b>${p.price}</b> <button>Show more</button><div hidden class=more>Weight ${p.weight} g</div><button>Add to cart</button>`;
        c.shadowRoot.querySelector('button').onclick = (e) => { setTimeout(()=>{ c.shadowRoot.querySelector('.more').hidden=false; }, 400); };
      }
      const back = document.createElement('button'); back.textContent='Return to Home'; main.appendChild(back);
      back.onclick = () => { const m = document.createElement('x-card'); main.appendChild(m);
        m.html = '<p>Discard your changes?</p><button>No</button><button>Yes</button>';
        m.shadowRoot.querySelectorAll('button')[1].onclick = () => location.hash='home'; };
    }
  }
}
customElements.define('app-shell', Shell);
</script></body></html>"""
# Settle fixtures. /beacon: a third-party (localhost vs 127.0.0.1) fetch and a first-party
# image every 200 ms forever, like analytics and lazy images on retail sites. /chain: four
# first-party fetches of 250 ms, 150 ms apart (400 ms start to start), then "Chain done".
# /late: "Late text" appears after 800 ms while the beacons keep firing.
BEACON = """<script>let n = 0; setInterval(() => { n++;
  fetch('http://localhost:' + location.port + '/b?' + n, {mode: 'no-cors'}).catch(() => {});
  new Image().src = '/px?' + n; }, 200);</script>"""
EXTRA = {
    "/beacon": "<!doctype html><title>Beacon</title><h1>Beacon page</h1>" + BEACON,
    "/chain": """<!doctype html><title>Chain</title><h1>Chain</h1><p id=s>step 0</p><script>
(async () => { for (let i = 1; i <= 4; i++) { await fetch('/api/slow?' + i);
  document.getElementById('s').textContent = 'step ' + i;
  if (i < 4) await new Promise(r => setTimeout(r, 150)); }
  document.body.insertAdjacentHTML('beforeend', '<p>Chain done</p>'); })();</script>""",
    "/long": "<!doctype html><title>Long</title><button id=more>More</button><div id=out></div><script>"
             "more.onclick = () => { for (let i = 0; i < 60; i++) out.insertAdjacentHTML('beforeend', "
             "'<p>Row ' + i + ' ' + 'x'.repeat(200) + '</p>'); };</script>",
    "/list": "<!doctype html><title>List</title><h1>Results</h1>" + "".join(
        '<div class="res card" data-sku="S%d"><h2>Product %d</h2><a href="/p/%d">open</a>%s'
        '<span class="tag">new</span><span class="tag">sale</span></div>'
        % (i, i, i, '<b class=price>$%d.00</b>' % (i * 3) if i % 3 else '') for i in range(1, 7)),
    "/late": "<!doctype html><title>Late</title><h1>Late</h1><script>setTimeout(() => "
             "document.body.insertAdjacentHTML('beforeend', '<p>Late text</p>'), 800)</script>" + BEACON,
}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/b', '/px'):
            self.send_response(204); self.send_header('Content-Length', '0'); self.end_headers(); return
        if path == '/api/slow':
            time.sleep(0.25); body, ct = b'{}', 'application/json'
        elif path in EXTRA:
            body, ct = EXTRA[path].encode(), 'text/html'
        elif self.path.startswith('/api/items'):
            time.sleep(1.2)
            body = json.dumps({"items":[{"name":f"Item {c}","price":f"${10*i+5}.00","weight":f"{500*i}"} for i,c in enumerate("ABCDEFG",1)]}).encode()
            ct='application/json'
        else:
            body=PAGE.encode(); ct='text/html'
        self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
