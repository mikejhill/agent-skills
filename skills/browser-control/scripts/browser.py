#!/usr/bin/env python3
"""browser.py - control the user's own running Chromium browser (Chrome, Edge, Brave).

Stdlib only (Python 3.8+). The broker holds a single WebSocket to the browser so the
user approves the browser's "Allow remote debugging?" prompt once per session, not once
per command. Every CLI call talks to the broker over a token-protected localhost socket.

    browser.py status                      endpoint detection + broker state
    browser.py start [--idle 900]          start broker (other commands auto-start it)
    browser.py stop                        stop broker (closes the WebSocket)
    browser.py targets [--all]             list tabs (id, type, title, url)
    browser.py send METHOD [JSON] [-p k=v] [-t TARGET]   raw CDP command
    browser.py eval EXPR -t TARGET         Runtime.evaluate (returnByValue, awaitPromise)
    browser.py open URL                    new tab, prints targetId
    browser.py nav URL -t TARGET           navigate and wait for load
    browser.py click SELECTOR -t TARGET    trusted mouse click at element center
    browser.py type TEXT -t TARGET [-s SELECTOR] [--replace]
    browser.py key Enter [ctrl+a ...] -t TARGET
    browser.py screenshot FILE -t TARGET [--full]
    browser.py pdf FILE -t TARGET [-p landscape=true ...]
    browser.py events [-t T] [-f PREFIX] [--since N] [--wait S] [--count N]
    browser.py mark                        print last event seq (use as --since)
    browser.py batch FILE|-                JSON lines: {"method":..,"params":..,"target":..}
    browser.py enable-help [--launch]      how to turn on remote debugging

TARGET = targetId (or unique prefix), or a case-insensitive substring of the tab's URL or
title. Browser-level methods (Target.*, Browser.*, SystemInfo.*, Storage.*) need no target.
"""
import argparse
import base64
import collections
import json
import os
import secrets
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.request

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
DEFAULT_IDLE = 900  # seconds without a CLI request before the broker exits
CONNECT_WAIT = 120  # seconds to wait for the user to approve the browser prompt
EVENT_BUFFER = 20000  # Network.enable on a busy SPA emits thousands of events per page
INFLIGHT_MAX_AGE = 10.0  # ignore requests open longer than this (long-poll, streaming)
INFLIGHT_SKIP = {"WebSocket", "EventSource", "Ping", "Media", "Manifest", "Prefetch"}

# In-page helper library, (re)defined idempotently before every eval, so it survives
# navigations and SPA reloads with no separate injection step. Everything pierces open
# shadow roots and same-origin iframes. Exposed to `eval` code as `__dt`.
DT_VERSION = 2
DT_JS = r"""if (!globalThis.__dt || globalThis.__dt.v !== %d) globalThis.__dt = (() => {
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'svg', 'SVG']);
  const CLICKABLE = 'a,button,summary,label,select,option,input[type=button],input[type=submit],' +
    'input[type=reset],input[type=radio],input[type=checkbox],[role=button],[role=link],[role=tab],' +
    '[role=menuitem],[role=option],[role=radio],[role=checkbox],[role=switch],[onclick],[tabindex]';
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const roots = (start = document) => {
    const out = [start];
    for (let i = 0; i < out.length; i++) {
      for (const el of out[i].querySelectorAll('*')) {
        if (el.shadowRoot) out.push(el.shadowRoot);
        if (el.tagName === 'IFRAME') { try { if (el.contentDocument) out.push(el.contentDocument); } catch (e) {} }
      }
    }
    return out;
  };
  const qsa = (sel, start) => roots(start).flatMap(r => [...r.querySelectorAll(sel)]);
  const vis = el => !el.checkVisibility || el.checkVisibility({ visibilityProperty: true, opacityProperty: false });
  const parentOf = n => n.parentNode instanceof ShadowRoot ? n.parentNode.host : (n.parentElement ||
    (n.parentNode && n.parentNode.defaultView && n.parentNode.defaultView.frameElement) || null);
  const label = el => norm(el.innerText || el.textContent) || norm(el.getAttribute && el.getAttribute('aria-label')) ||
    norm(el.value) || norm(el.title) || norm(el.getAttribute && el.getAttribute('alt'));
  const deepText = (node, hidden) => {
    const out = []; const vcache = new Map();
    const shown = el => { if (hidden) return true; if (!vcache.has(el)) vcache.set(el, vis(el)); return vcache.get(el); };
    const walk = n => {
      if (n.nodeType === 3) { const t = norm(n.textContent); if (t && (!n.parentElement || shown(n.parentElement))) out.push(t); return; }
      if (n.nodeType === 1) {
        if (SKIP.has(n.tagName)) return;
        if (n.tagName === 'INPUT' && shown(n)) {
          const t = (n.type || '').toLowerCase();
          if (t === 'radio' || t === 'checkbox') out.push(n.checked ? '[x]' : '[ ]');
          else if (!['hidden', 'button', 'submit', 'reset'].includes(t) && n.value) out.push('[' + n.value + ']');
        }
        if (n.tagName === 'SELECT' && shown(n)) { const o = n.selectedOptions[0]; out.push('[' + norm(o && o.text) + ' v]'); return; }
        if (n.tagName === 'IFRAME') { try { if (n.contentDocument) walk(n.contentDocument.body || n.contentDocument); } catch (e) {} return; }
        if (n.shadowRoot) walk(n.shadowRoot);
      }
      for (const c of n.childNodes) walk(c);
    };
    walk(node || document.body || document.documentElement);
    return out.join('\n');
  };
  const text = (o = {}) => {
    let t = deepText(o.selector ? qsa(o.selector)[0] : null, o.hidden);
    if (o.after) { const i = t.indexOf(o.after); t = i < 0 ? '' : t.slice(i + o.after.length); }
    if (o.before) { const i = t.indexOf(o.before); if (i >= 0) t = t.slice(0, i); }
    if (o.grep) { const re = new RegExp(o.grep, 'i'); const ls = t.split('\n'); const c = o.context || 0; const keep = new Set();
      ls.forEach((l, i) => { if (re.test(l)) for (let j = i - c; j <= i + c; j++) keep.add(j); });
      t = ls.filter((l, i) => keep.has(i)).join('\n'); }
    const total = t.length, off = o.offset || 0, max = o.max || 8000;
    return { text: t.slice(off, off + max), total, more: Math.max(0, total - off - max) };
  };
  const find = (o = {}) => {
    let c = o.selector ? qsa(o.selector) : qsa(CLICKABLE);
    if (!o.hidden) c = c.filter(vis);
    if (o.text != null) {
      const want = norm(o.text), lw = want.toLowerCase();
      const exact = c.filter(e => label(e) === want);
      c = exact.length || o.exact ? exact : c.filter(e => label(e).toLowerCase().includes(lw));
      // innermost match only: drop ancestors whose label merely contains a matching child
      c = c.filter(e => !c.some(d => d !== e && e.contains(d)));
    }
    if (o.within) {
      const w = norm(o.within).toLowerCase();
      const depth = e => { let n = e; for (let d = 0; n && d < 8; d++, n = parentOf(n)) { if (deepText(n, true).toLowerCase().includes(w)) return d; } return -1; };
      c = c.map(e => [e, depth(e)]).filter(x => x[1] >= 0).sort((a, b) => a[1] - b[1]).map(x => x[0]);
    }
    return c;
  };
  const hit = el => {
    el.scrollIntoView({ block: 'center', inline: 'center' });
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) return null;
    const x = r.x + r.width / 2, y = r.y + r.height / 2;
    let top = document.elementFromPoint(x, y);
    while (top && top.shadowRoot) { const inner = top.shadowRoot.elementFromPoint(x, y); if (!inner || inner === top) break; top = inner; }
    for (let n = top; n; n = parentOf(n)) if (n === el) return [x, y];
    for (let n = el; n; n = parentOf(n)) if (n === top) return [x, y];
    return null;
  };
  const pick = (o = {}) => {
    const c = find(o), i = o.index || 0, el = c[i];
    if (!el) {
      const seen = qsa(CLICKABLE).filter(vis).map(label).filter(Boolean);
      return { found: 0, matches: c.length, candidates: [...new Set(seen)].slice(0, 40) };
    }
    __dt.last = el;
    return { found: 1, matches: c.length, tag: el.tagName.toLowerCase(), label: label(el).slice(0, 80), xy: hit(el) };
  };
  const click = (o = {}) => { const p = pick(o); if (p.found) __dt.last.click(); return p; };
  const has = (o = {}) => {
    if (o.url && !location.href.includes(o.url)) return false;
    if (o.selector && !qsa(o.selector).some(vis)) return false;
    if (o.text && !deepText().includes(o.text)) return false;
    if (o.gone && deepText().includes(o.gone)) return false;
    if (o.goneSelector && qsa(o.goneSelector).some(vis)) return false;
    return true;
  };
  const BUSY = '[aria-busy=true],[role=progressbar],progress,[class*=spinner i],[class*=loading i],' +
    '[class*=loader i],[class*=skeleton i]';
  // Page signature for settle-waits. A visible spinner or "Loading..." makes every poll
  // unique, so the page never looks quiet while one shows (e.g. a timer fetches later).
  const sig = () => {
    const t = deepText();
    const busy = /(^|\n)[^\n]{0,30}\b(loading|please wait)\b/i.test(t) ||
      qsa(BUSY).some(e => vis(e) && e.getBoundingClientRect().width > 0);
    return busy ? 'busy:' + Math.random() :
      location.href + '|' + t.length + '|' + performance.getEntriesByType('resource').length;
  };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  return { v: %d, roots, qsa, vis, label, deepText, text, find, pick, click, has, sig, sleep };
})();
void 0;
""" % (DT_VERSION, DT_VERSION)


def with_dt(expr):
    return DT_JS + expr


# --------------------------------------------------------------------------- paths

def state_dir():
    if os.environ.get("BROWSER_CONTROL_HOME"):  # isolate test brokers from the real one
        base = os.environ["BROWSER_CONTROL_HOME"]
    elif IS_WIN:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    elif IS_MAC:
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    d = os.path.join(base, "browser-control")
    os.makedirs(d, exist_ok=True)
    return d


STATE_FILE = lambda: os.path.join(state_dir(), "broker.json")
LOG_FILE = lambda: os.path.join(state_dir(), "broker.log")


def profile_dirs():
    """(name, user-data-dir) candidates, most common first."""
    h = os.path.expanduser("~")
    if IS_WIN:
        la = os.environ.get("LOCALAPPDATA") or os.path.join(h, "AppData", "Local")
        rel = [("edge", r"Microsoft\Edge\User Data"), ("chrome", r"Google\Chrome\User Data"),
               ("edge-beta", r"Microsoft\Edge Beta\User Data"), ("edge-dev", r"Microsoft\Edge Dev\User Data"),
               ("edge-canary", r"Microsoft\Edge SxS\User Data"), ("chrome-beta", r"Google\Chrome Beta\User Data"),
               ("chrome-canary", r"Google\Chrome SxS\User Data"), ("brave", r"BraveSoftware\Brave-Browser\User Data"),
               ("chromium", r"Chromium\User Data")]
        return [(n, os.path.join(la, p)) for n, p in rel]
    if IS_MAC:
        b = os.path.join(h, "Library", "Application Support")
        rel = [("chrome", "Google/Chrome"), ("edge", "Microsoft Edge"), ("chrome-beta", "Google/Chrome Beta"),
               ("chrome-canary", "Google/Chrome Canary"), ("edge-beta", "Microsoft Edge Beta"),
               ("brave", "BraveSoftware/Brave-Browser"), ("chromium", "Chromium")]
        return [(n, os.path.join(b, p)) for n, p in rel]
    c = os.environ.get("XDG_CONFIG_HOME") or os.path.join(h, ".config")
    rel = [("chrome", "google-chrome"), ("edge", "microsoft-edge"), ("chromium", "chromium"),
           ("chrome-beta", "google-chrome-beta"), ("edge-beta", "microsoft-edge-beta"),
           ("brave", "BraveSoftware/Brave-Browser")]
    return [(n, os.path.join(c, p)) for n, p in rel]


# ------------------------------------------------------------------ endpoint discovery

def port_open(port, host="127.0.0.1", timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def discover(browser=None, port=None):
    """Return list of live endpoints: {name, port, ws, source}."""
    found = []
    if port:
        ws = None
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2) as r:
                ws = json.load(r).get("webSocketDebuggerUrl")
        except Exception:
            pass
        if ws or port_open(port):
            found.append({"name": "port%d" % port, "port": port, "ws": ws, "source": "--port"})
        return found
    for name, d in profile_dirs():
        if browser and name != browser:
            continue
        f = os.path.join(d, "DevToolsActivePort")
        try:
            with open(f, encoding="utf-8") as fh:
                lines = fh.read().split()
            p, path = int(lines[0]), lines[1]
        except Exception:
            continue
        if port_open(p):  # file can be stale after a crash
            found.append({"name": name, "port": p, "ws": "ws://127.0.0.1:%d%s" % (p, path), "source": f})
    if not found and not browser:  # classic --remote-debugging-port without a profile file we know
        for p in (9222, 9229):
            try:
                with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % p, timeout=1) as r:
                    v = json.load(r)
                found.append({"name": v.get("Browser", "port%d" % p), "port": p,
                              "ws": v.get("webSocketDebuggerUrl"), "source": "http://127.0.0.1:%d" % p})
            except Exception:
                pass
    return found


ENABLE_HELP = """Remote debugging is not enabled (no live DevToolsActivePort / debug port found).

Ask the user to enable it in the browser they want automated:
  Edge:   open  edge://inspect/#remote-debugging
  Chrome: open  chrome://inspect/#remote-debugging
  (Brave: brave://inspect/#remote-debugging)
and turn on "Allow remote debugging for this browser instance". No restart needed.
The browser then shows an "Allow remote debugging?" prompt when the broker connects;
the user must click Allow (once per broker session).

Older browsers without that page: restart with --remote-debugging-port=9222 and a
non-default --user-data-dir (Chrome 136+ ignores the flag on the default profile).
"""


# ---------------------------------------------------------------- minimal WebSocket

class WSClosed(Exception):
    pass


class WebSocket:
    """RFC 6455 client: text frames, fragmentation, ping/pong, close. No TLS (localhost)."""

    def __init__(self, url, timeout=None):
        assert url.startswith("ws://"), url
        hostport, _, path = url[5:].partition("/")
        host, _, port = hostport.partition(":")
        self.sock = socket.create_connection((host, int(port or 80)), timeout=10)
        self.sock.settimeout(timeout)  # approval prompt may hold the handshake open
        key = base64.b64encode(os.urandom(16)).decode()
        # No Origin header: Chrome only enforces --remote-allow-origins when Origin is sent.
        req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WSClosed("connection closed during handshake (prompt denied?)")
            buf += chunk
        head, _, self.rest = buf.partition(b"\r\n\r\n")
        status = head.split(b"\r\n", 1)[0].decode(errors="replace")
        if " 101 " not in status + " ":
            raise WSClosed("handshake failed: %s" % status)
        self.sock.settimeout(None)
        self.wlock = threading.Lock()

    def _read(self, n):
        out = bytearray()
        if self.rest:
            out += self.rest[:n]
            self.rest = self.rest[n:]
        while len(out) < n:
            chunk = self.sock.recv(min(1 << 20, n - len(out)))
            if not chunk:
                raise WSClosed("socket closed")
            out += chunk
        return bytes(out)

    def _frame(self, opcode, payload):
        hdr = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126); hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127); hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        hdr += mask
        if n:
            # XOR mask via big-int arithmetic: fast enough for multi-MB payloads.
            m = (mask * (n // 4 + 1))[:n]
            payload = (int.from_bytes(payload, "big") ^ int.from_bytes(m, "big")).to_bytes(n, "big")
        with self.wlock:
            self.sock.sendall(bytes(hdr) + payload)

    def send(self, text):
        self._frame(0x1, text.encode("utf-8"))

    def recv(self):
        parts, op0 = [], None
        while True:
            b0, b1 = self._read(2)
            fin, op, n = b0 & 0x80, b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            mask = self._read(4) if b1 & 0x80 else None
            data = self._read(n) if n else b""
            if mask:
                data = bytes(c ^ mask[i % 4] for i, c in enumerate(data))
            if op == 0x8:
                try:
                    self._frame(0x8, data[:2])
                except OSError:
                    pass
                raise WSClosed("closed by browser")
            if op == 0x9:
                self._frame(0xA, data); continue
            if op == 0xA:
                continue
            if op in (0x1, 0x2):
                op0 = op
            parts.append(data)
            if fin:
                return b"".join(parts).decode("utf-8", errors="replace")

    def close(self):
        try:
            self._frame(0x8, struct.pack(">H", 1000))
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


# ------------------------------------------------------------------------- broker

class Broker:
    def __init__(self, endpoint, idle, token):
        self.endpoint, self.idle, self.token = endpoint, idle, token
        self.ws = None
        self.next_id = 0
        self.pending = {}  # id -> [Event, response]
        self.plock = threading.Lock()
        self.events = collections.deque(maxlen=EVENT_BUFFER)
        self.seq = 0
        self.econd = threading.Condition()
        self.sessions = {}  # targetId -> sessionId
        self.sess_target = {}  # sessionId -> targetId
        self.inflight = {}  # sessionId -> {requestId: start time}, once Network is enabled
        self.net_on = set()  # sessionIds with Network.enable sent by the broker or a client
        self.attach_lock = threading.Lock()
        self.last_activity = time.time()
        self.stopping = threading.Event()
        self.state = "connecting"
        self.error = None
        self.started = time.time()
        self.exit_reason = None

    def log(self, *a):
        try:
            with open(LOG_FILE(), "a", encoding="utf-8") as f:
                f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
        except OSError:
            pass

    # --- browser side
    def connect(self):
        try:
            self.ws = WebSocket(self.endpoint["ws"], timeout=CONNECT_WAIT)
        except Exception as e:
            self.state, self.error = "failed", str(e)
            self.log("connect failed:", e)
            self.stopping.set()
            return
        self.state = "connected"
        self.log("connected", self.endpoint["ws"])
        threading.Thread(target=self.reader, daemon=True).start()

    def reader(self):
        try:
            while not self.stopping.is_set():
                msg = json.loads(self.ws.recv())
                if "id" in msg:
                    with self.plock:
                        slot = self.pending.pop(msg["id"], None)
                    if slot:
                        slot[1] = msg
                        slot[0].set()
                    continue
                m, sid = msg.get("method", ""), msg.get("sessionId")
                if m == "Target.detachedFromTarget":
                    s = msg.get("params", {}).get("sessionId")
                    t = self.sess_target.pop(s, None)
                    if t:
                        self.sessions.pop(t, None)
                    self.inflight.pop(s, None)
                    self.net_on.discard(s)
                elif sid and m.startswith("Network."):
                    p = msg.get("params", {})
                    fl = self.inflight.setdefault(sid, {})
                    if m == "Network.requestWillBeSent" and p.get("type") not in INFLIGHT_SKIP:
                        fl[p.get("requestId")] = time.time()
                    elif m in ("Network.loadingFinished", "Network.loadingFailed"):
                        fl.pop(p.get("requestId"), None)
                with self.econd:
                    self.seq += 1
                    self.events.append({"seq": self.seq, "t": round(time.time(), 3), "method": m,
                                        "targetId": self.sess_target.get(sid), "sessionId": sid,
                                        "params": msg.get("params", {})})
                    self.econd.notify_all()
        except Exception as e:
            if not self.stopping.is_set():
                self.log("reader ended:", e)
                self.state, self.error = "disconnected", str(e)
                self.stopping.set()
        with self.plock:  # fail anything still waiting
            for slot in self.pending.values():
                slot[1] = {"error": {"message": "browser connection closed"}}
                slot[0].set()
            self.pending.clear()

    def call(self, method, params=None, session=None, timeout=30):
        if self.state != "connected":
            return {"error": {"message": "broker not connected (%s) %s" % (self.state, self.error or "")}}
        with self.plock:
            self.next_id += 1
            mid = self.next_id
            slot = [threading.Event(), None]
            self.pending[mid] = slot
        msg = {"id": mid, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        self.ws.send(json.dumps(msg))
        if not timeout:
            with self.plock:
                self.pending.pop(mid, None)
            return {}
        if not slot[0].wait(timeout):
            with self.plock:
                self.pending.pop(mid, None)
            return {"error": {"message": "timeout after %ss waiting for %s" % (timeout, method)}}
        return slot[1]

    def targets(self):
        r = self.call("Target.getTargets")
        return r.get("result", {}).get("targetInfos", []) if "result" in r else []

    def resolve(self, spec):
        """targetId / prefix / url-or-title substring -> targetInfo (pages first)."""
        ts = self.targets()
        if not ts:
            raise ValueError("no targets (is the broker connected?)")
        for t in ts:
            if t["targetId"] == spec:
                return t
        s = spec.lower()
        pref = [t for t in ts if t["targetId"].lower().startswith(s)]
        if len(pref) == 1:
            return pref[0]
        sub = [t for t in ts if s in t.get("url", "").lower() or s in t.get("title", "").lower()]
        pages = [t for t in sub if t.get("type") == "page"] or sub
        if len(pages) == 1:
            return pages[0]
        if not pages:
            raise ValueError("no target matches %r; run `browser.py targets`" % spec)
        raise ValueError("%r is ambiguous (%d matches): %s" % (spec, len(pages), ", ".join(
            "%s %s" % (t["targetId"][:8], t.get("url", "")[:60]) for t in pages[:6])))

    def session_for(self, spec):
        with self.attach_lock:
            return self._session_for(spec)

    def _session_for(self, spec):
        t = self.resolve(spec)
        tid = t["targetId"]
        if tid in self.sessions:
            return tid, self.sessions[tid]
        r = self.call("Target.attachToTarget", {"targetId": tid, "flatten": True})
        if "error" in r:
            raise ValueError("attach failed: %s" % r["error"].get("message"))
        sid = r["result"]["sessionId"]
        self.sessions[tid], self.sess_target[sid] = sid, tid
        return tid, sid

    # --- CLI side
    def handle(self, req):
        op = req.get("op")
        if op == "status":
            return {"state": self.state, "error": self.error, "endpoint": self.endpoint,
                    "pid": os.getpid(), "uptime": round(time.time() - self.started),
                    "idle_timeout": self.idle, "idle_for": round(time.time() - self.last_activity),
                    "sessions": len(self.sessions), "event_seq": self.seq}
        if op == "stop":
            self.exit_reason = "stop requested"
            self.stopping.set()
            return {"stopped": True}
        if op == "send":
            sess, tid = req.get("sessionId"), None
            if req.get("target"):
                tid, sess = self.session_for(req["target"])
            if req.get("nowait"):  # fire-and-forget (cleanup calls)
                self.call(req["method"], req.get("params"), sess, 0)
                return {}
            r = self.call(req["method"], req.get("params"), sess, req.get("timeout", 30))
            if sess and "error" not in r and req["method"] in ("Network.enable", "Network.disable"):
                (self.net_on.add if req["method"] == "Network.enable" else self.net_on.discard)(sess)
                self.inflight.pop(sess, None)
            if tid:
                r["targetId"] = tid
            return r
        if op == "netwatch":
            tid, sid = self.session_for(req["target"])
            self.ensure_network(sid)
            return {"targetId": tid, "network": True}
        if op == "wait":
            return self.wait(req)
        if op == "targets":
            return {"targets": self.targets()}
        if op == "resolve":
            tid, sid = self.session_for(req["target"])
            return {"targetId": tid, "sessionId": sid}
        if op == "events":
            return self.get_events(req)
        return {"error": {"message": "unknown op %r" % op}}

    def ensure_network(self, sid):
        if sid not in self.net_on:
            r = self.call("Network.enable", {}, sid)
            if "error" in r:
                raise ValueError("Network.enable failed: %s" % r["error"].get("message"))
            self.net_on.add(sid)

    def evaluate(self, sid, expr, timeout=10):
        r = self.call("Runtime.evaluate", {"expression": with_dt(expr), "returnByValue": True,
                                           "awaitPromise": True}, sid, timeout)
        res = r.get("result", {})
        if "error" in r or res.get("exceptionDetails"):
            return None, (r.get("error") or res["exceptionDetails"]).get("text") or "evaluate failed"
        return res.get("result", {}).get("value"), None

    def wait(self, req):
        """Poll until `cond` holds, then (if settle) until the page is quiet.

        Quiet = no in-flight XHR/fetch/document requests and no change in URL, visible text
        length or completed-resource count for `quiet` seconds. Errors from evaluate (page
        mid-navigation, context destroyed) count as "not ready", not failure.
        """
        tid, sid = self.session_for(req["target"])
        settle = req.get("settle", True)
        if settle:
            self.ensure_network(sid)
        cond = req.get("cond")
        quiet, timeout = float(req.get("quiet", 0.5)), float(req.get("timeout", 15))
        t0 = time.time()
        end = t0 + timeout
        met_at = None
        last_sig, last_change = None, t0
        polls = 0
        while True:
            now = time.time()
            polls += 1
            if met_at is None:
                ok, err = (True, None) if not cond else self.evaluate(sid, cond)
                if ok and not err:
                    met_at = now
                    last_change = now
            if met_at is not None:
                if not settle:
                    break
                sig, err = self.evaluate(sid, "__dt.sig()")
                busy = sum(1 for st in self.inflight.get(sid, {}).values() if now - st < INFLIGHT_MAX_AGE)
                if err or busy or sig != last_sig:
                    last_sig, last_change = sig, now
                elif now - last_change >= quiet:
                    break
            if now >= end:
                return {"targetId": tid, "ok": False, "cond_met": met_at is not None,
                        "waited": round(now - t0, 2), "inflight": len(self.inflight.get(sid, {}))}
            time.sleep(0.1)
        return {"targetId": tid, "ok": True, "waited": round(time.time() - t0, 2)}

    def get_events(self, req):
        since = req.get("since", 0)
        prefixes = tuple(p.strip() for p in (req.get("filter") or "").split(",")) or ("",)
        tid = None
        if req.get("target"):
            tid = self.resolve(req["target"])["targetId"]
        want, deadline = req.get("count", 0), time.time() + float(req.get("wait", 0))

        def match():
            return [e for e in self.events if e["seq"] > since and e["method"].startswith(prefixes)
                    and (tid is None or e["targetId"] == tid)]
        with self.econd:
            got = match()
            while (not got or (want and len(got) < want)) and time.time() < deadline \
                    and not self.stopping.is_set():
                self.econd.wait(min(1.0, max(0.01, deadline - time.time())))
                got = match()
        if want:
            got = got[:want]
        if req.get("limit"):
            got = got[-int(req["limit"]):]
        return {"events": got, "last_seq": self.seq}

    def serve_client(self, conn):
        try:
            conn.settimeout(None)
            f = conn.makefile("rwb")
            req = json.loads(f.readline() or b"{}")
            if req.get("token") != self.token:
                resp = {"error": {"message": "bad token"}}
            else:
                self.last_activity = time.time()
                try:
                    resp = self.handle(req)
                except ValueError as e:
                    resp = {"error": {"message": str(e)}}
                except Exception as e:
                    self.log("handler error:", repr(e))
                    resp = {"error": {"message": "broker error: %r" % e}}
                self.last_activity = time.time()
            f.write((json.dumps(resp) + "\n").encode())
            f.flush()
        except Exception as e:
            self.log("client error:", repr(e))
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(16)
        srv.settimeout(1.0)
        state = {"pid": os.getpid(), "port": srv.getsockname()[1], "token": self.token,
                 "endpoint": self.endpoint, "started": self.started}
        tmp = STATE_FILE() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_FILE())
        self.log("broker pid %d listening on %d, idle %ss" % (os.getpid(), state["port"], self.idle))
        threading.Thread(target=self.connect, daemon=True).start()
        try:
            while not self.stopping.is_set():
                if time.time() - self.last_activity > self.idle:
                    self.exit_reason = "idle timeout"
                    break
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=self.serve_client, args=(conn,), daemon=True).start()
            # linger briefly so a failed-connect status can still be read by the CLI
            if self.state == "failed":
                end = time.time() + 5
                while time.time() < end:
                    try:
                        conn, _ = srv.accept()
                        self.serve_client(conn)
                    except socket.timeout:
                        pass
        finally:
            self.stopping.set()
            if self.ws:
                self.ws.close()
            srv.close()
            try:  # close before removing: Windows can't delete an open file
                with open(STATE_FILE(), encoding="utf-8") as f:
                    mine = json.load(f).get("pid") == os.getpid()
                if mine:
                    os.remove(STATE_FILE())
            except (OSError, ValueError):
                pass
            self.log("broker exit (%s)" % (self.exit_reason or self.state))


# ------------------------------------------------------------------------ client

class CLIError(Exception):
    pass


def read_state():
    try:
        with open(STATE_FILE(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def rpc(req, state=None, timeout=None):
    state = state or read_state()
    if not state:
        raise CLIError("broker not running")
    req = dict(req, token=state["token"])
    try:
        s = socket.create_connection(("127.0.0.1", state["port"]), timeout=5)
    except OSError:
        raise CLIError("broker not reachable (stale state file?)")
    with s:
        s.settimeout(timeout)
        f = s.makefile("rwb")
        try:
            f.write((json.dumps(req) + "\n").encode())
            f.flush()
            line = f.readline()
        except OSError:
            line = b""
    if not line:
        raise CLIError("broker closed the connection")
    return json.loads(line)


def broker_alive(state=None):
    try:
        return rpc({"op": "status"}, state, timeout=5)
    except CLIError:
        return None


def spawn_broker(endpoint, idle):
    token = secrets.token_hex(16)
    args = [os.path.abspath(__file__), "_broker", "--idle", str(idle), "--token", token,
            "--endpoint", json.dumps(endpoint)]
    exe = sys.executable
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              close_fds=True, cwd=state_dir())
    if IS_WIN:
        # pythonw.exe has no console; flags also prevent a console window from flashing
        # and detach the broker from the caller's console / job.
        w = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(w):
            exe = w
        kw["creationflags"] = (0x08000000 | 0x00000008 | 0x00000200)  # NO_WINDOW|DETACHED|NEW_GROUP
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            kw["startupinfo"] = si
        except AttributeError:
            pass
    else:
        kw["start_new_session"] = True
    subprocess.Popen([exe] + args, **kw)


def ensure_broker(args, quiet=False):
    st = read_state()
    if st:
        s = broker_alive(st)
        want_port, want_browser = getattr(args, "port", None), getattr(args, "browser", None)
        ep = (s or {}).get("endpoint") or {}
        if s and ((want_port and ep.get("port") != want_port) or (want_browser and ep.get("name") != want_browser)):
            raise CLIError("a broker is already running for %s (port %s); run `browser.py stop` "
                           "before targeting another browser" % (ep.get("name"), ep.get("port")))
        if s and s.get("state") in ("connected", "connecting"):
            if s["state"] == "connecting":
                return wait_connected(st, quiet)
            return st
    eps = discover(getattr(args, "browser", None), getattr(args, "port", None))
    if not eps:
        raise CLIError(ENABLE_HELP)
    ep = eps[0]
    if len(eps) > 1 and not quiet:
        sys.stderr.write("multiple browsers found (%s); using %s. Pass --browser to choose.\n"
                         % (", ".join(e["name"] for e in eps), ep["name"]))
    if not ep.get("ws"):
        raise CLIError("found port %s but no WebSocket URL" % ep["port"])
    if True:  # always tell the agent, even on auto-start: the user may need to click Allow
        sys.stderr.write("starting broker for %s (port %s). If the browser shows "
                         "'Allow remote debugging?', click Allow.\n" % (ep["name"], ep["port"]))
    spawn_broker(ep, getattr(args, "idle", None) or DEFAULT_IDLE)
    end = time.time() + 10
    while time.time() < end:
        st = read_state()
        if st and broker_alive(st):
            return wait_connected(st, quiet)
        time.sleep(0.1)
    raise CLIError("broker did not start; see %s" % LOG_FILE())


def wait_connected(st, quiet):
    end = time.time() + CONNECT_WAIT + 5
    while time.time() < end:
        s = broker_alive(st)
        if not s:
            raise CLIError("broker exited; see %s" % LOG_FILE())
        if s["state"] == "connected":
            return st
        if s["state"] != "connecting":
            raise CLIError("browser connection %s: %s" % (s["state"], s.get("error")))
        time.sleep(0.2)
    raise CLIError("timed out waiting for the browser to accept the connection "
                   "(was the 'Allow remote debugging?' prompt approved?)")


def parse_params(args):
    params = {}
    raw = getattr(args, "params", None)
    if raw:
        if raw == "-":
            raw = sys.stdin.read()
        elif raw.startswith("@"):
            with open(raw[1:], encoding="utf-8-sig") as f:
                raw = f.read()
        params = json.loads(raw)
    for kv in getattr(args, "p", None) or []:
        k, _, v = kv.partition("=")
        try:
            val = json.loads(v)
        except ValueError:
            val = v
        # CDP string ids look numeric (requestId "1234.56", loaderId, frameId): keep the
        # literal for *Id keys unless it is a plain integer (nodeId, backendNodeId).
        if (k.endswith("Id") and isinstance(val, float)) or val in (float("inf"), float("-inf")) or val != val:
            val = v
        cur = params
        keys = k.split(".")
        for part in keys[:-1]:
            cur = cur.setdefault(part, {})
        cur[keys[-1]] = val
    return params


def out(obj, args=None):
    s = json.dumps(obj, indent=2 if getattr(args, "pretty", False) else None, ensure_ascii=False)
    try:
        print(s)
    except UnicodeEncodeError:
        print(json.dumps(obj, indent=2))


def check(r):
    if "error" in r:
        e = r["error"]
        if "code" not in e:  # broker-side error (target resolution, timeout, ...)
            raise CLIError(e.get("message"))
        raise CLIError("CDP error %s: %s%s" % (e.get("code"), e.get("message"),
                                               (" (%s)" % e["data"]) if e.get("data") else ""))
    return r.get("result", r)


_BROKER = []  # memo: one broker check per process (matters for `run`)


def broker(args):
    if not _BROKER:
        _BROKER.append(ensure_broker(args, quiet=True))
    return _BROKER[0]


def send(args, method, params=None, target=None, timeout=30):
    return rpc({"op": "send", "method": method, "params": params or {}, "target": target,
                "timeout": timeout}, broker(args), timeout=timeout + 15)


def js_eval(args, expr, target, timeout=30):
    """Evaluate with the __dt helpers available; return the JSON value (one round trip)."""
    r = check(send(args, "Runtime.evaluate", {"expression": with_dt(expr), "awaitPromise": True,
                                              "returnByValue": True, "userGesture": True}, target, timeout))
    if r.get("exceptionDetails"):
        ed = r["exceptionDetails"]
        raise CLIError("JS exception: %s" % (ed.get("exception", {}).get("description") or ed.get("text")))
    return r.get("result", {}).get("value")


def broker_wait(args, target, cond=None, settle=True, quiet=0.5, timeout=15):
    r = rpc({"op": "wait", "target": target, "cond": cond, "settle": settle, "quiet": quiet,
             "timeout": timeout}, broker(args), timeout=timeout + 15)
    if "error" in r:
        raise CLIError(r["error"].get("message"))
    return r


# --- commands

def cmd_status(args):
    eps = discover(args.browser, args.port)
    st = read_state()
    b = broker_alive(st) if st else None
    out({"endpoints": eps, "broker": b or "not running"}, args)
    if not eps and not b:
        sys.stderr.write("\n" + ENABLE_HELP)
        return 3


def cmd_start(args):
    st = ensure_broker(args)
    out(rpc({"op": "status"}, st), args)


def cmd_stop(args):
    st = read_state()
    if not st or not broker_alive(st):
        try:
            os.remove(STATE_FILE())
        except OSError:
            pass
        out({"stopped": False, "note": "broker was not running"}, args)
        return
    rpc({"op": "stop"}, st)
    end = time.time() + 5
    while time.time() < end and broker_alive(st):
        time.sleep(0.1)
    out({"stopped": True}, args)


def cmd_targets(args):
    st = ensure_broker(args, quiet=True)
    ts = rpc({"op": "targets"}, st)["targets"]
    if not args.all:
        ts = [t for t in ts if t.get("type") == "page"]
    out([{"id": t["targetId"], "type": t["type"], "title": t.get("title", "")[:80],
          "url": t.get("url", "")[:200], "attached": t.get("attached")} for t in ts], args)


def cmd_send(args):
    r = send(args, args.method, parse_params(args), args.target, args.timeout)
    if args.raw:
        out(r, args)
    else:
        out(check(r), args)


SERIALIZE_FN = """async function () {
  let v = this;
  if (v && typeof v.then === 'function') v = await v;
  const d = x => x instanceof Element ? '<' + x.tagName.toLowerCase() + (x.id ? '#' + x.id : '') +
    (typeof x.className === 'string' && x.className ? '.' + x.className.trim().split(/\\s+/).join('.') : '') + '>' : String(x);
  if (v instanceof Node || v === window) return d(v);
  if (v instanceof Error) return String(v);
  if (typeof NodeList !== 'undefined' && (v instanceof NodeList || v instanceof HTMLCollection)) return [...v].map(d);
  if (Array.isArray(v) && v.some(x => x instanceof Node)) return v.map(x => x instanceof Node ? d(x) : x);
  return v;
}"""


def cmd_eval(args):
    expr = args.expr
    if expr == "-":
        expr = sys.stdin.read()
    elif expr.startswith("@"):
        with open(expr[1:], encoding="utf-8-sig") as f:
            expr = f.read()
    t = args.target
    # replMode: top-level await and let-redeclaration across calls. Helpers are prepended
    # (cheap no-op once defined), so __dt survives navigations without re-injection.
    r = check(send(args, "Runtime.evaluate", {"expression": expr if args.no_helpers else with_dt(expr),
                                              "awaitPromise": True, "userGesture": True, "replMode": True,
                                              "objectGroup": "browsercli"}, t, args.timeout))
    if r.get("exceptionDetails"):
        ed = r["exceptionDetails"]
        raise CLIError("JS exception: %s" % (ed.get("exception", {}).get("description") or ed.get("text")))
    res = r.get("result", {})
    if res.get("type") == "undefined":
        return out(None, args)
    if "objectId" not in res:  # primitive: done in one round trip
        return out(res.get("value", res.get("unserializableValue")), args)
    try:  # object: serialize in-page (awaits returned promises, describes DOM nodes)
        v = send(args, "Runtime.callFunctionOn", {"objectId": res["objectId"], "returnByValue": True,
                                                  "awaitPromise": True, "functionDeclaration": SERIALIZE_FN},
                 t, args.timeout)
        vr = v.get("result", {})
        if "error" in v or vr.get("exceptionDetails"):  # cyclic / not serializable
            return out({k: res[k] for k in ("type", "subtype", "className", "description") if k in res}, args)
        out(vr["result"].get("value"), args)
    finally:
        rpc({"op": "send", "method": "Runtime.releaseObjectGroup", "params": {"objectGroup": "browsercli"},
             "target": t, "nowait": True}, broker(args))


def cmd_open(args):
    r = check(send(args, "Target.createTarget", {"url": args.url, "background": args.background}))
    out(r, args)


def wait_event(st, method, target, since, timeout):
    r = rpc({"op": "events", "filter": method, "target": target, "since": since,
             "wait": timeout, "count": 1}, st, timeout=timeout + 15)
    return r["events"][0] if r.get("events") else None


def cmd_nav(args):
    st = broker(args)
    check(send(args, "Page.enable", {}, args.target))
    if not args.no_wait and not args.no_settle:
        rpc({"op": "netwatch", "target": args.target}, st)
    seq = rpc({"op": "events", "since": 10 ** 12}, st)["last_seq"]
    r = check(send(args, "Page.navigate", {"url": args.url}, args.target))
    if r.get("errorText"):
        raise CLIError("navigation failed: %s" % r["errorText"])
    ev = None
    same_doc = not r.get("loaderId")  # hash/history navigation: no load event will fire
    if not args.no_wait and not same_doc:
        ev = wait_event(st, "Page.loadEventFired", args.target, seq, args.timeout)
    res = {"frameId": r.get("frameId"), "loaded": (bool(ev) or same_doc) if not args.no_wait else None}
    if args.no_wait:
        return out(res, args)
    out(after_action(args, res), args)


def cmd_screenshot(args):
    p = {"format": "jpeg" if args.file.lower().endswith((".jpg", ".jpeg")) else "png"}
    if args.full:
        m = check(send(args, "Page.getLayoutMetrics", {}, args.target))
        cs = m.get("cssContentSize") or m["contentSize"]
        p.update(captureBeyondViewport=True,
                 clip={"x": 0, "y": 0, "width": cs["width"], "height": cs["height"], "scale": 1})
    r = check(send(args, "Page.captureScreenshot", p, args.target, args.timeout))
    data = base64.b64decode(r["data"])
    with open(args.file, "wb") as f:
        f.write(data)
    out({"file": os.path.abspath(args.file), "bytes": len(data)}, args)


KEYS = {  # key: (code, windowsVirtualKeyCode, text)
    "Enter": ("Enter", 13, "\r"), "Tab": ("Tab", 9, ""), "Escape": ("Escape", 27, ""),
    "Backspace": ("Backspace", 8, ""), "Delete": ("Delete", 46, ""), "Space": ("Space", 32, " "),
    "ArrowUp": ("ArrowUp", 38, ""), "ArrowDown": ("ArrowDown", 40, ""), "ArrowLeft": ("ArrowLeft", 37, ""),
    "ArrowRight": ("ArrowRight", 39, ""), "Home": ("Home", 36, ""), "End": ("End", 35, ""),
    "PageUp": ("PageUp", 33, ""), "PageDown": ("PageDown", 34, ""),
}
MODS = {"alt": 1, "ctrl": 2, "control": 2, "meta": 4, "cmd": 4, "shift": 8}


def js_str(v):
    return json.dumps(v)


def wait_opts(args):
    """Condition object for __dt.has() from --for-* style flags, or None."""
    o = {k: getattr(args, a) for k, a in (("text", "for_text"), ("selector", "for_selector"),
                                          ("gone", "for_gone"), ("url", "for_url"))
         if getattr(args, a, None)}
    return "__dt.has(%s)" % json.dumps(o) if o else None


def after_action(args, res):
    """Shared tail for click/key/nav: wait for a condition and/or quiet, then optional text."""
    cond = wait_opts(args)
    if cond or not args.no_settle:
        w = broker_wait(args, args.target, cond, settle=not args.no_settle, quiet=args.quiet,
                        timeout=args.timeout)
        res["waited"] = w["waited"]
        if not w["ok"]:
            res["timeout"] = "condition not met" if cond and not w.get("cond_met") else "page still busy"
    if getattr(args, "show", None) is not None:
        o = {"max": args.max}
        if args.show:
            o["after"] = args.show
        res["text"] = js_eval(args, "__dt.text(%s)" % json.dumps(o), args.target)["text"]
    return res


def cmd_click(args):
    if not args.selector and args.text is None:
        raise CLIError("give a CSS SELECTOR or --text TEXT")
    o = {"selector": args.selector, "text": args.text, "index": args.index, "exact": args.exact,
         "within": args.within, "hidden": args.hidden}
    o = {k: v for k, v in o.items() if v not in (None, False)}
    if not args.no_settle:  # start network tracking before the click, not after it
        rpc({"op": "netwatch", "target": args.target}, broker(args))
    p = js_eval(args, "__dt.pick(%s)" % json.dumps(o), args.target)
    if not p.get("found"):
        what = args.selector or args.text
        raise CLIError("no visible element matches %r (index %d of %d). Clickable labels: %s"
                       % (what, args.index, p.get("matches", 0), "; ".join(p.get("candidates", []))[:1500]))
    res = {"clicked": p["label"], "tag": p["tag"], "matches": p["matches"]}
    if p.get("xy") and not args.dom:
        x, y = p["xy"]
        base = {"x": x, "y": y, "button": "left", "clickCount": args.count}
        for typ in ("mouseMoved", "mousePressed", "mouseReleased"):
            check(send(args, "Input.dispatchMouseEvent", dict(base, type=typ), args.target))
        res["via"] = "mouse"
    else:  # covered, zero-size, or --dom: element.click() (untrusted, but no hit-testing)
        js_eval(args, "__dt.last.click()", args.target)
        res["via"] = "dom"
    out(after_action(args, res), args)


def cmd_text(args):
    o = {"selector": args.selector, "after": args.after, "before": args.before, "grep": args.grep,
         "context": args.context, "max": args.max, "offset": args.offset, "hidden": args.hidden}
    r = js_eval(args, "__dt.text(%s)" % json.dumps({k: v for k, v in o.items() if v}), args.target)
    sys.stdout.write(r["text"] + "\n")
    if r["more"]:
        sys.stdout.write("[... %d more chars; total %d; use --offset %d]\n"
                         % (r["more"], r["total"], (args.offset or 0) + args.max))


def cmd_wait(args):
    cond = wait_opts(args)
    if args.ms:
        time.sleep(args.ms / 1000.0)
    w = broker_wait(args, args.target, cond, settle=not args.no_settle, quiet=args.quiet, timeout=args.timeout)
    res = {"ok": w["ok"], "waited": w["waited"]}
    if not w["ok"]:
        res["timeout"] = "condition not met" if cond and not w.get("cond_met") else "page still busy"
    if args.show is not None:
        o = {"max": args.max}
        if args.show:
            o["after"] = args.show
        res["text"] = js_eval(args, "__dt.text(%s)" % json.dumps(o), args.target)["text"]
    out(res, args)
    return 0 if w["ok"] else 1


def responses(args):
    r = rpc({"op": "events", "target": args.target, "filter": "Network.responseReceived",
             "since": args.since}, broker(args))
    if "error" in r:
        raise CLIError(r["error"]["message"])
    rows = []
    for e in r["events"]:
        if e["method"] != "Network.responseReceived":
            continue
        resp = e["params"].get("response", {})
        rows.append({"id": e["params"].get("requestId"), "type": e["params"].get("type"),
                     "status": resp.get("status"), "mime": resp.get("mimeType"), "url": resp.get("url", "")})
    return rows, r["last_seq"]


def cmd_net(args):
    rows, last = responses(args)
    if not args.all:
        rows = [x for x in rows if x["type"] in ("XHR", "Fetch", "Document")]
    if args.grep:
        rows = [x for x in rows if args.grep.lower() in x["url"].lower()]
    rows = rows[-args.limit:] if args.limit else rows
    for x in rows:
        sys.stdout.write("%s %s %s %s %s\n" % (x["id"], x["status"], x["type"], (x["mime"] or "")[:24],
                                               x["url"][:args.width]))
    sys.stdout.write("[%d responses; last_seq %d]\n" % (len(rows), last))


def cmd_body(args):
    rid = args.request
    if args.url:
        rows, _ = responses(argparse.Namespace(target=args.target, since=0))
        hits = [x for x in rows if rid.lower() in x["url"].lower()]
        if not hits:
            raise CLIError("no buffered response URL contains %r (Network must be enabled before "
                           "the request: click/nav/wait do that, or `send Network.enable`)" % rid)
        rid = hits[-1]["id"]
    r = check(send(args, "Network.getResponseBody", {"requestId": rid}, args.target))
    body = base64.b64decode(r["body"]) if r.get("base64Encoded") else r["body"].encode("utf-8")
    if args.out:
        with open(args.out, "wb") as f:
            f.write(body)
        return out({"requestId": rid, "file": os.path.abspath(args.out), "bytes": len(body)}, args)
    txt = body.decode("utf-8", errors="replace")
    more = len(txt) - args.max
    sys.stdout.write(txt[:args.max] + ("\n[... %d more chars; use -o FILE]\n" % more if more > 0 else "\n"))


TARGETED = {"send", "eval", "nav", "click", "type", "key", "screenshot", "pdf", "events", "text",
            "wait", "net", "body", "batch"}


def cmd_run(args):
    """Run CLI steps (one per line, shell-style quoting) in one process with shared -t."""
    import shlex
    src = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8-sig")
    with src:
        lines = [l.strip() for l in src.read().splitlines()]
    steps = [l for l in lines if l and not l.startswith("#")]
    glob = []
    for flag in ("browser", "port"):
        if getattr(args, flag, None):
            glob += ["--" + flag, str(getattr(args, flag))]
    rc = 0
    for i, line in enumerate(steps, 1):
        toks = shlex.split(line, posix=True)
        if toks and toks[0] in ("run", "start", "stop"):
            raise CLIError("step %d: %r is not allowed inside run" % (i, toks[0]))
        if args.target and toks and toks[0] in TARGETED and "-t" not in toks and "--target" not in toks:
            toks += ["-t", args.target]
        sys.stdout.write("## %d %s\n" % (i, line[:120]))
        sys.stdout.flush()
        code = main(glob + toks, nested=True)
        sys.stdout.flush()
        if code:
            rc = code
            if not args.keep_going:
                sys.stdout.write("## stopped at step %d (exit %d)\n" % (i, code))
                break
    return rc


def cmd_type(args):
    if args.selector:
        js = ("(() => { const e = document.querySelector(%s); if (!e) return false; e.focus(); "
              "if (%s && 'value' in e) { e.select && e.select(); } return true; })()"
              % (js_str(args.selector), "true" if args.replace else "false"))
        r = check(send(args, "Runtime.evaluate", {"expression": js, "returnByValue": True}, args.target))
        if not r.get("result", {}).get("value"):
            raise CLIError("no element matches %r" % args.selector)
    check(send(args, "Input.insertText", {"text": args.text}, args.target))
    out({"typed": len(args.text)}, args)


def cmd_key(args):
    for combo in args.keys:
        parts = combo.split("+")
        key, mods = parts[-1], 0
        for m in parts[:-1]:
            mods |= MODS.get(m.lower(), 0)
        if key in KEYS:
            code, vk, text = KEYS[key]
        elif len(key) == 1:
            code = ("Key" + key.upper()) if key.isalpha() else ("Digit" + key if key.isdigit() else "")
            vk, text = ord(key.upper()), key
        else:
            raise CLIError("unknown key %r (use Enter, Tab, Escape, ArrowDown, a, ...)" % key)
        if mods & ~8:  # with ctrl/alt/meta, don't insert text
            text = ""
        ev = {"key": key, "code": code, "windowsVirtualKeyCode": vk, "modifiers": mods}
        check(send(args, "Input.dispatchKeyEvent", dict(ev, type="keyDown" if text else "rawKeyDown",
                                                       **({"text": text} if text else {})), args.target))
        check(send(args, "Input.dispatchKeyEvent", dict(ev, type="keyUp"), args.target))
    args.no_settle = not args.settle
    out(after_action(args, {"pressed": args.keys}), args)


def cmd_pdf(args):
    r = check(send(args, "Page.printToPDF", dict({"printBackground": True}, **parse_params(args)),
                   args.target, args.timeout))
    data = base64.b64decode(r["data"])
    with open(args.file, "wb") as f:
        f.write(data)
    out({"file": os.path.abspath(args.file), "bytes": len(data)}, args)


def cmd_events(args):
    st = ensure_broker(args, quiet=True)
    r = rpc({"op": "events", "target": args.target, "filter": args.filter, "since": args.since,
             "wait": args.wait, "count": args.count, "limit": args.limit}, st,
            timeout=args.wait + 15)
    if "error" in r:
        raise CLIError(r["error"]["message"])
    if args.methods_only:
        r["events"] = [{"seq": e["seq"], "method": e["method"], "targetId": e["targetId"]} for e in r["events"]]
    elif not args.full:
        for e in r["events"]:
            e.pop("sessionId", None)
    out(r, args)


def cmd_mark(args):
    st = ensure_broker(args, quiet=True)
    out({"last_seq": rpc({"op": "events", "since": 10 ** 12}, st)["last_seq"]}, args)


def cmd_batch(args):
    st = ensure_broker(args, quiet=True)
    src = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8-sig")
    results = []
    with src:
        for line in src:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            c = json.loads(line)
            r = rpc({"op": "send", "method": c["method"], "params": c.get("params", {}),
                     "target": c.get("target", args.target), "timeout": c.get("timeout", 30)},
                    st, timeout=c.get("timeout", 30) + 15)
            results.append({"method": c["method"], **({"error": r["error"]} if "error" in r
                                                       else {"result": r.get("result")})})
            if "error" in r and not args.keep_going:
                break
    out(results, args)
    return 1 if any("error" in r for r in results) else 0


def cmd_enable_help(args):
    sys.stdout.write(ENABLE_HELP)
    if args.launch:
        url = {"edge": "edge://inspect/#remote-debugging", "chrome": "chrome://inspect/#remote-debugging"}[args.launch]
        if IS_WIN:
            exe = "msedge" if args.launch == "edge" else "chrome"
            subprocess.Popen('start "" %s "%s"' % (exe, url), shell=True)
        elif IS_MAC:
            app = "Microsoft Edge" if args.launch == "edge" else "Google Chrome"
            subprocess.Popen(["open", "-a", app, url])
        else:
            subprocess.Popen(["microsoft-edge" if args.launch == "edge" else "google-chrome", url])
        print("\nOpened %s in %s." % (url, args.launch))


def cmd_broker(args):
    Broker(json.loads(args.endpoint), args.idle, args.token).run()


def add_wait_flags(p, settle_default=True):
    g = p.add_argument_group("waiting (replaces sleeps)")
    g.add_argument("--for-text", metavar="TEXT", help="wait until visible text contains TEXT")
    g.add_argument("--for-selector", metavar="CSS", help="wait until a visible element matches CSS")
    g.add_argument("--for-gone", metavar="TEXT", help="wait until TEXT is no longer visible (spinners)")
    g.add_argument("--for-url", metavar="SUBSTR", help="wait until location.href contains SUBSTR")
    if settle_default:
        g.add_argument("--no-settle", action="store_true", help="skip waiting for network/DOM quiet")
    else:
        g.add_argument("--settle", action="store_true", help="wait for network/DOM quiet afterwards")
    g.add_argument("--quiet", type=float, default=0.5, help="quiet period in seconds (default 0.5)")
    g.add_argument("--timeout", type=float, default=15, help="max seconds to wait (default 15)")
    g.add_argument("--show", nargs="?", const="", metavar="AFTER",
                   help="print visible text afterwards (optionally only after marker AFTER)")
    g.add_argument("--max", type=int, default=4000, help="max chars for --show (default 4000)")


def main(argv=None, nested=False):
    ap = argparse.ArgumentParser(prog="browser", description=__doc__.split("\n\n")[0])
    ap.add_argument("--browser", help="profile name: edge, chrome, brave, edge-beta, ... (default: first live)")
    ap.add_argument("--port", type=int, help="explicit debug port (classic --remote-debugging-port)")
    ap.add_argument("--compact", action="store_true", help=argparse.SUPPRESS)  # now the default
    ap.add_argument("--pretty", action="store_true", help="indented JSON output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def tgt(p, required=False):
        p.add_argument("-t", "--target", required=required,
                       help="targetId, id prefix, or URL/title substring")

    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("start"); p.add_argument("--idle", type=int, default=DEFAULT_IDLE,
                                                help="exit after N idle seconds (default 900)")
    p.set_defaults(fn=cmd_start)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    p = sub.add_parser("targets"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_targets)
    p = sub.add_parser("send"); p.add_argument("method"); p.add_argument("params", nargs="?",
                                                                         help="JSON, @file.json, or - for stdin")
    p.add_argument("-p", action="append", metavar="KEY=VALUE", help="param (repeatable; dotted keys; JSON values)")
    tgt(p); p.add_argument("--timeout", type=float, default=30)
    p.add_argument("--raw", action="store_true", help="print full response envelope")
    p.set_defaults(fn=cmd_send)
    p = sub.add_parser("eval"); p.add_argument("expr", help="JS expression, @file.js, or -"); tgt(p, True)
    p.add_argument("--timeout", type=float, default=30)
    p.add_argument("--no-helpers", action="store_true", help="skip defining the __dt helper library")
    p.set_defaults(fn=cmd_eval)
    p = sub.add_parser("open"); p.add_argument("url"); p.add_argument("--background", action="store_true")
    p.set_defaults(fn=cmd_open)
    p = sub.add_parser("nav"); p.add_argument("url"); tgt(p, True)
    p.add_argument("--no-wait", action="store_true", help="return right after Page.navigate")
    add_wait_flags(p); p.set_defaults(fn=cmd_nav)
    p = sub.add_parser("screenshot"); p.add_argument("file"); tgt(p, True)
    p.add_argument("--full", action="store_true"); p.add_argument("--timeout", type=float, default=60)
    p.set_defaults(fn=cmd_screenshot)
    p = sub.add_parser("click"); p.add_argument("selector", nargs="?", help="CSS selector (pierces shadow DOM)")
    tgt(p, True)
    p.add_argument("--text", help="match clickable elements by visible label (exact first, then substring)")
    p.add_argument("--index", type=int, default=0, help="pick the Nth match (0-based)")
    p.add_argument("--exact", action="store_true", help="no substring fallback for --text")
    p.add_argument("--within", metavar="TEXT", help="only matches whose nearby container contains TEXT")
    p.add_argument("--hidden", action="store_true", help="include invisible elements")
    p.add_argument("--dom", action="store_true", help="element.click() instead of a trusted mouse click")
    p.add_argument("--count", type=int, default=1, help="2 = double-click")
    add_wait_flags(p); p.set_defaults(fn=cmd_click)
    p = sub.add_parser("type"); p.add_argument("text"); tgt(p, True)
    p.add_argument("-s", "--selector", help="focus this element first")
    p.add_argument("--replace", action="store_true", help="select existing text first (overwrite)")
    p.set_defaults(fn=cmd_type)
    p = sub.add_parser("key"); p.add_argument("keys", nargs="+", help="Enter, Tab, Escape, ArrowDown, ctrl+a, ...")
    tgt(p, True); add_wait_flags(p, settle_default=False); p.set_defaults(fn=cmd_key)
    p = sub.add_parser("text", help="visible text, piercing shadow DOM and same-origin iframes")
    tgt(p, True)
    p.add_argument("-s", "--selector", help="only inside the first element matching CSS")
    p.add_argument("--after", help="only text after the first occurrence of this marker")
    p.add_argument("--before", help="only text before this marker")
    p.add_argument("--grep", metavar="REGEX", help="only matching lines (case-insensitive)")
    p.add_argument("-C", "--context", type=int, default=0, help="lines of context around --grep hits")
    p.add_argument("--max", type=int, default=8000, help="max chars (default 8000)")
    p.add_argument("--offset", type=int, default=0, help="skip this many chars (paging)")
    p.add_argument("--hidden", action="store_true", help="include invisible text")
    p.set_defaults(fn=cmd_text)
    p = sub.add_parser("wait", help="wait for a condition and/or network+DOM quiet (instead of sleep)")
    tgt(p, True); add_wait_flags(p)
    p.add_argument("--ms", type=int, default=0, help="fixed delay first (rarely needed)")
    p.set_defaults(fn=cmd_wait)
    p = sub.add_parser("net", help="recent responses (XHR/fetch/document by default)"); tgt(p, True)
    p.add_argument("--since", type=int, default=0); p.add_argument("--grep", metavar="SUBSTR")
    p.add_argument("--all", action="store_true", help="include scripts, images, css, ...")
    p.add_argument("--limit", type=int, default=40); p.add_argument("--width", type=int, default=140)
    p.set_defaults(fn=cmd_net)
    p = sub.add_parser("body", help="response body by requestId (or --url substring)"); tgt(p, True)
    p.add_argument("request"); p.add_argument("--url", action="store_true", help="REQUEST is a URL substring")
    p.add_argument("-o", "--out", help="write to file instead of stdout")
    p.add_argument("--max", type=int, default=8000); p.set_defaults(fn=cmd_body)
    p = sub.add_parser("run", help="run CLI steps from FILE or - (one per line) in one process")
    p.add_argument("file"); tgt(p); p.add_argument("--keep-going", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("pdf"); p.add_argument("file"); tgt(p, True)
    p.add_argument("-p", action="append", metavar="KEY=VALUE", help="Page.printToPDF param")
    p.add_argument("--timeout", type=float, default=60); p.set_defaults(fn=cmd_pdf)
    p = sub.add_parser("events"); tgt(p)
    p.add_argument("-f", "--filter", default="", help="method prefix(es), comma-separated, e.g. Network.,Page.loadEventFired")
    p.add_argument("--since", type=int, default=0, help="only events with seq > N (use last_seq)")
    p.add_argument("--wait", type=float, default=0, help="block up to N seconds for a match")
    p.add_argument("--count", type=int, default=0, help="wait until N matches; return first N")
    p.add_argument("--limit", type=int, default=0, help="return only the last N matches")
    p.add_argument("--full", action="store_true", help="include sessionId")
    p.add_argument("--methods-only", action="store_true", help="omit params (overview)")
    p.set_defaults(fn=cmd_events)
    sub.add_parser("mark", help="print last_seq; pass it to events --since before triggering an action"
                   ).set_defaults(fn=cmd_mark)
    p = sub.add_parser("batch"); p.add_argument("file"); tgt(p)
    p.add_argument("--keep-going", action="store_true"); p.set_defaults(fn=cmd_batch)
    p = sub.add_parser("enable-help"); p.add_argument("--launch", choices=["edge", "chrome"])
    p.set_defaults(fn=cmd_enable_help)
    p = sub.add_parser("_broker"); p.add_argument("--idle", type=int); p.add_argument("--token")
    p.add_argument("--endpoint"); p.set_defaults(fn=cmd_broker)

    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        if nested:
            return e.code or 2
        raise
    if IS_WIN and not nested:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        return args.fn(args) or 0
    except CLIError as e:
        sys.stderr.write("error: %s\n" % e)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
