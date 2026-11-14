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
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path.startswith('/api/items'):
            time.sleep(1.2)
            body = json.dumps({"items":[{"name":f"Item {c}","price":f"${10*i+5}.00","weight":f"{500*i}"} for i,c in enumerate("ABCDEFG",1)]}).encode()
            ct='application/json'
        else:
            body=PAGE.encode(); ct='text/html'
        self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()
