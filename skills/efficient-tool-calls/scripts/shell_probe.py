#!/usr/bin/env python3
"""shell_probe.py - measure how long each local shell takes to start, and cache the answer.

Shell startup cost depends on the machine: Git Bash can start in 60 ms on one Windows box
and 600 ms on another (antivirus, MSYS fork emulation, network home dirs), and a PowerShell
profile can add a second. Agent harnesses spawn a fresh shell per tool call, so the faster
shell saves that difference on every call. Measure once per machine; reuse the result.

    python shell_probe.py                 cached result if under 7 days old, else measure
    python shell_probe.py --force         measure now
    python shell_probe.py --max-age-days N
    python shell_probe.py --runs N        timed runs per shell (default 5, plus 1 warm-up)

Prints one JSON object: per-shell median/p90 startup in ms, the fastest POSIX shell, the
fastest PowerShell, and a recommendation. Stdlib only, Python 3.8+. Cache:
$EFFICIENT_TOOL_CALLS_CACHE, else the user cache dir (efficient-tool-calls/shell-probe.json).
"""
import argparse
import json
import os
import math
import signal
import socket
import statistics
import subprocess
import sys
import threading
import time

IS_WIN = os.name == "nt"
CACHE_VERSION = 1
CLOSE_MS = 150  # differences below this are small next to model and harness time per call


def cache_path():
    if os.environ.get("EFFICIENT_TOOL_CALLS_CACHE"):
        return os.environ["EFFICIENT_TOOL_CALLS_CACHE"]
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "efficient-tool-calls", "shell-probe.json")


def find_exe(name, skip=None):
    """Look `name` up on PATH, absolute directories only. Unlike shutil.which on Windows
    Python <= 3.11, never the current directory, so a workspace can't plant a `pwsh.exe`."""
    exts = [""]
    if IS_WIN:
        exts = [e for e in os.environ.get("PATHEXT", ".EXE;.CMD;.BAT").split(";") if e]
        if os.path.splitext(name)[1]:
            exts = [""] + exts
    cwd = os.path.normcase(os.path.abspath(os.getcwd()))
    for d in os.environ.get("PATH", "").split(os.pathsep):
        d = d.strip('"')
        if not d or not os.path.isabs(d) or os.path.normcase(os.path.abspath(d)) == cwd:
            continue
        for e in exts:
            f = os.path.join(d, name + e)
            if os.path.isfile(f) and os.access(f, os.X_OK) and not (skip and skip(f)):
                return f
    return None


def win_bash():
    """Git Bash, not the WSL launcher in System32 (that starts a Linux VM)."""
    wsl = lambda f: "system32" in f.lower()
    cands = []
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
                 os.environ.get("LOCALAPPDATA") and os.path.join(os.environ["LOCALAPPDATA"], "Programs")):
        if root and os.path.isabs(root):  # an unset variable must not become a relative path
            cands.append(os.path.join(root, "Git", "bin", "bash.exe"))
    cands.append(find_exe("bash", skip=wsl))  # keep searching PATH past the WSL launcher
    for c in cands:
        if c and os.path.isfile(c) and not wsl(c):
            return c
    return None


def candidates():
    """(name, family, argv) for each shell found. argv runs an empty command."""
    out = []
    posix = [("bash", win_bash())] if IS_WIN else [(n, find_exe(n)) for n in ("bash", "zsh")]
    for name, p in posix:  # what agent shell tools run (not sh)
        if p:
            out.append((name, "posix", [p, "-c", "true"]))
            out.append((name + " (login)", "posix-login", [p, "-lc", "true"]))
    # Windows PowerShell 5.1 only stands in when pwsh 7 is missing: agent tools run pwsh, and
    # 5.1 lacks `&&`, ternaries and UTF-8 defaults, so a faster 5.1 start is no reason to use it.
    pw = find_exe("pwsh")
    for name in ("pwsh", "powershell") if IS_WIN else ("pwsh",):
        p = find_exe(name)
        if p:
            fam = "powershell" if name == "pwsh" or not pw else "powershell-5"
            out.append((name, fam, [p, "-NoProfile", "-NonInteractive", "-Command", "exit"]))
            out.append((name + " (profile)", fam + "-profile", [p, "-NonInteractive", "-Command", "exit"]))
    if IS_WIN:
        p = find_exe("cmd")
        if p:
            out.append(("cmd", "cmd", [p, "/d", "/c", "exit"]))
    return out


def run_once(argv, kw, limit=30):
    """Seconds until the shell exits, or None if it fails. Waits on the process itself
    (no timeout polling, which adds up to 50 ms on POSIX); a timer enforces `limit`."""
    kw = dict(kw)
    if IS_WIN:
        kw["creationflags"] = kw.get("creationflags", 0) | 0x00000200  # CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True  # own process group, so a timeout ends its children too
    try:
        t = time.perf_counter()
        p = subprocess.Popen(argv, **kw)
    except OSError:
        return None

    def kill_tree():
        try:
            if IS_WIN:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            else:
                os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            p.kill()
    killer = threading.Timer(limit, kill_tree)
    killer.start()
    try:
        code = p.wait()
        dt = time.perf_counter() - t
    finally:
        killer.cancel()
    return dt if code == 0 else None


def time_one(argv, runs):
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if IS_WIN:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    ts = []
    for i in range(runs + 1):
        dt = run_once(argv, kw)
        if dt is None:  # failed to start, nonzero exit, or killed: don't recommend it
            return None
        if i:  # first run is a warm-up (disk cache)
            ts.append(dt * 1000)
    ts.sort()
    return {"median_ms": round(statistics.median(ts)), "p90_ms": round(ts[max(0, math.ceil(0.9 * len(ts)) - 1)])}


def recommend(shells):
    def best(fam):
        c = [(v["median_ms"], k) for k, v in shells.items() if v.get("family") == fam]
        return min(c) if c else None

    def extra(name, suffix):  # same executable, other launch mode
        v = shells.get("%s (%s)" % (name, suffix))
        return v["median_ms"] - shells[name]["median_ms"] if v else None

    px, ps = best("posix"), best("powershell")
    r = {"fastest_posix": px[1] if px else None, "fastest_powershell": ps[1] if ps else None}
    if px and ps:
        diff = ps[0] - px[0]
        if abs(diff) < CLOSE_MS:
            r["recommendation"] = ("either: startup differs by %d ms; choose by task (POSIX tools vs cmdlets)"
                                   % abs(diff))
        else:
            fast, slow = (px[1], ps[1]) if diff > 0 else (ps[1], px[1])
            r["recommendation"] = ("prefer %s for general command-line work: %d ms faster to start per call "
                                   "than %s; keep %s for work only it can do" % (fast, abs(diff), slow, slow))
    else:
        found = [k for k, v in shells.items() if "-" not in v.get("family", "")]
        if px or ps:
            r["recommendation"] = ("no %s found to compare with; measured: %s"
                                   % ("PowerShell" if px else "POSIX shell", ", ".join(found)))
        elif found:
            r["recommendation"] = "no POSIX shell or PowerShell found; measured: %s" % ", ".join(found)
        else:
            r["recommendation"] = "no shell found"
    if ps:
        cost = extra(ps[1], "profile")
        if cost is not None and cost >= CLOSE_MS:
            r["profile_cost_ms"] = cost
    if px:
        cost = extra(px[1], "login")
        if cost is not None and cost >= CLOSE_MS:
            r["login_cost_ms"] = cost
    return r


def measure(runs):
    shells = {}
    for name, fam, argv in candidates():
        t = time_one(argv, runs)
        if t:
            shells[name] = dict(t, family=fam, path=argv[0])
    res = {"v": CACHE_VERSION, "host": socket.gethostname(), "platform": sys.platform,
           "measured_at": int(time.time()), "runs": runs, "shells": shells}
    res.update(recommend(shells))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="measure even if a fresh cached result exists")
    ap.add_argument("--max-age-days", type=float, default=7, help="reuse a cached result up to this old (7)")
    ap.add_argument("--runs", type=int, default=5, help="timed runs per shell (5)")
    a = ap.parse_args(argv)
    path = cache_path()
    if not a.force:
        try:
            with open(path, encoding="utf-8") as f:
                c = json.load(f)
            ok = (isinstance(c, dict) and c.get("v") == CACHE_VERSION and c.get("host") == socket.gethostname()
                  and c.get("platform") == sys.platform and isinstance(c.get("measured_at"), (int, float))
                  and isinstance(c.get("shells"), dict))
            if ok and time.time() - c["measured_at"] < a.max_age_days * 86400:
                c["cached"] = True
                print(json.dumps(c))
                return 0
        except (OSError, ValueError):
            pass
    res = measure(max(1, a.runs))
    try:
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(res, f)
    except OSError as e:
        sys.stderr.write("warning: could not write cache %s: %s\n" % (path, e))
    res["cached"] = False
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
