#!/usr/bin/env python3
"""devtools.py - Chrome DevTools Protocol CLI backed by one persistent, windowless broker.

Stdlib only (Python 3.8+). The broker holds a single WebSocket to the browser so the
user approves the browser's "Allow remote debugging?" prompt once per session, not once
per command. Every CLI call talks to the broker over a token-protected localhost socket.

    devtools.py status                      endpoint detection + broker state
    devtools.py start [--idle 900]          start broker (other commands auto-start it)
    devtools.py stop                        stop broker (closes the WebSocket)
    devtools.py targets [--all]             list tabs (id, type, title, url)
    devtools.py send METHOD [JSON] [-p k=v] [-t TARGET]   raw CDP command
    devtools.py eval EXPR -t TARGET         Runtime.evaluate (returnByValue, awaitPromise)
    devtools.py open URL                    new tab, prints targetId
    devtools.py nav URL -t TARGET           navigate and wait for load
    devtools.py click SELECTOR -t TARGET    trusted mouse click at element center
    devtools.py type TEXT -t TARGET [-s SELECTOR] [--replace]
    devtools.py key Enter [ctrl+a ...] -t TARGET
    devtools.py screenshot FILE -t TARGET [--full]
    devtools.py pdf FILE -t TARGET [-p landscape=true ...]
    devtools.py events [-t T] [-f PREFIX] [--since N] [--wait S] [--count N]
    devtools.py mark                        print last event seq (use as --since)
    devtools.py batch FILE|-                JSON lines: {"method":..,"params":..,"target":..}
    devtools.py enable-help [--launch]      how to turn on remote debugging

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


# --------------------------------------------------------------------------- paths

def state_dir():
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    elif IS_MAC:
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    d = os.path.join(base, "browser-devtools")
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
        self.events = collections.deque(maxlen=5000)
        self.seq = 0
        self.econd = threading.Condition()
        self.sessions = {}  # targetId -> sessionId
        self.sess_target = {}  # sessionId -> targetId
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
            raise ValueError("no target matches %r; run `devtools.py targets`" % spec)
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
            r = self.call(req["method"], req.get("params"), sess, req.get("timeout", 30))
            if tid:
                r["targetId"] = tid
            return r
        if op == "targets":
            return {"targets": self.targets()}
        if op == "resolve":
            tid, sid = self.session_for(req["target"])
            return {"targetId": tid, "sessionId": sid}
        if op == "events":
            return self.get_events(req)
        return {"error": {"message": "unknown op %r" % op}}

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
        f.write((json.dumps(req) + "\n").encode())
        f.flush()
        line = f.readline()
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
        cur = params
        keys = k.split(".")
        for part in keys[:-1]:
            cur = cur.setdefault(part, {})
        cur[keys[-1]] = val
    return params


def out(obj, args=None):
    s = json.dumps(obj, indent=None if getattr(args, "compact", False) else 2, ensure_ascii=False)
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


def send(args, method, params=None, target=None, timeout=30):
    st = ensure_broker(args, quiet=True)
    return rpc({"op": "send", "method": method, "params": params or {}, "target": target,
                "timeout": timeout}, st, timeout=timeout + 15)


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


def cmd_eval(args):
    expr = args.expr
    if expr == "-":
        expr = sys.stdin.read()
    elif expr.startswith("@"):
        with open(expr[1:], encoding="utf-8-sig") as f:
            expr = f.read()
    t = args.target
    r = check(send(args, "Runtime.evaluate", {"expression": expr, "awaitPromise": True, "userGesture": True,
                                              "replMode": True, "objectGroup": "devtoolscli"}, t, args.timeout))
    if r.get("exceptionDetails"):
        ed = r["exceptionDetails"]
        msg = ed.get("exception", {}).get("description") or ed.get("text")
        raise CLIError("JS exception: %s" % msg)
    res = r.get("result", {})
    if res.get("subtype") == "promise":  # replMode doesn't await a returned promise
        r = check(send(args, "Runtime.awaitPromise", {"promiseObjectId": res["objectId"]}, t, args.timeout))
        if r.get("exceptionDetails"):
            ed = r["exceptionDetails"]
            raise CLIError("JS exception: %s" % (ed.get("exception", {}).get("description") or ed.get("text")))
        res = r.get("result", {})
    if res.get("type") == "undefined":
        return out(None, args)
    if "objectId" not in res:  # primitive
        return out(res.get("value", res.get("unserializableValue")), args)
    try:
        if res.get("subtype") in ("node", "error", "proxy", "window"):
            return out({k: res[k] for k in ("type", "subtype", "className", "description") if k in res}, args)
        v = send(args, "Runtime.callFunctionOn", {"objectId": res["objectId"], "returnByValue": True,
                                                  "functionDeclaration": "function(){return this}"}, t)
        if "error" in v or v["result"].get("exceptionDetails"):  # cyclic / not serializable
            return out({k: res[k] for k in ("type", "subtype", "className", "description") if k in res}, args)
        out(v["result"]["result"].get("value"), args)
    finally:
        send(args, "Runtime.releaseObjectGroup", {"objectGroup": "devtoolscli"}, t)


def cmd_open(args):
    r = check(send(args, "Target.createTarget", {"url": args.url, "background": args.background}))
    out(r, args)


def wait_event(st, method, target, since, timeout):
    r = rpc({"op": "events", "filter": method, "target": target, "since": since,
             "wait": timeout, "count": 1}, st, timeout=timeout + 15)
    return r["events"][0] if r.get("events") else None


def cmd_nav(args):
    st = ensure_broker(args, quiet=True)
    check(send(args, "Page.enable", {}, args.target))
    seq = rpc({"op": "events", "since": 10 ** 12}, st)["last_seq"]
    r = check(send(args, "Page.navigate", {"url": args.url}, args.target))
    if r.get("errorText"):
        raise CLIError("navigation failed: %s" % r["errorText"])
    ev = None
    if not args.no_wait:
        ev = wait_event(st, "Page.loadEventFired", args.target, seq, args.timeout)
    out({"frameId": r.get("frameId"), "loaded": bool(ev) if not args.no_wait else None}, args)


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


def cmd_click(args):
    js = ("(() => { const e = document.querySelector(%s); if (!e) return null; "
          "e.scrollIntoView({block: 'center', inline: 'center'}); const r = e.getBoundingClientRect(); "
          "return [r.x + r.width / 2, r.y + r.height / 2]; })()" % js_str(args.selector))
    r = check(send(args, "Runtime.evaluate", {"expression": js, "returnByValue": True}, args.target))
    xy = r.get("result", {}).get("value")
    if not xy:
        raise CLIError("no element matches %r" % args.selector)
    x, y = xy
    base = {"x": x, "y": y, "button": "left", "clickCount": args.count}
    for typ in ("mouseMoved", "mousePressed", "mouseReleased"):
        check(send(args, "Input.dispatchMouseEvent", dict(base, type=typ), args.target))
    out({"clicked": args.selector, "x": round(x), "y": round(y)}, args)


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
    out({"pressed": args.keys}, args)


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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="devtools", description=__doc__.split("\n\n")[0])
    ap.add_argument("--browser", help="profile name: edge, chrome, brave, edge-beta, ... (default: first live)")
    ap.add_argument("--port", type=int, help="explicit debug port (classic --remote-debugging-port)")
    ap.add_argument("--compact", action="store_true", help="single-line JSON output")
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
    p.add_argument("--timeout", type=float, default=30); p.set_defaults(fn=cmd_eval)
    p = sub.add_parser("open"); p.add_argument("url"); p.add_argument("--background", action="store_true")
    p.set_defaults(fn=cmd_open)
    p = sub.add_parser("nav"); p.add_argument("url"); tgt(p, True)
    p.add_argument("--timeout", type=float, default=30); p.add_argument("--no-wait", action="store_true")
    p.set_defaults(fn=cmd_nav)
    p = sub.add_parser("screenshot"); p.add_argument("file"); tgt(p, True)
    p.add_argument("--full", action="store_true"); p.add_argument("--timeout", type=float, default=60)
    p.set_defaults(fn=cmd_screenshot)
    p = sub.add_parser("click"); p.add_argument("selector"); tgt(p, True)
    p.add_argument("--count", type=int, default=1, help="2 = double-click"); p.set_defaults(fn=cmd_click)
    p = sub.add_parser("type"); p.add_argument("text"); tgt(p, True)
    p.add_argument("-s", "--selector", help="focus this element first")
    p.add_argument("--replace", action="store_true", help="select existing text first (overwrite)")
    p.set_defaults(fn=cmd_type)
    p = sub.add_parser("key"); p.add_argument("keys", nargs="+", help="Enter, Tab, Escape, ArrowDown, ctrl+a, ...")
    tgt(p, True); p.set_defaults(fn=cmd_key)
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

    args = ap.parse_args(argv)
    if IS_WIN:
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
