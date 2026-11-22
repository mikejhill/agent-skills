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
    python shell_probe.py --profiles      also time login bash/zsh and PowerShell with profile
                                          (runs your startup scripts runs+1 times each)

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
import tempfile
import subprocess
import sys
import threading
import time

IS_WIN = os.name == "nt"
CACHE_VERSION = 2
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


def _norm(p):
    return os.path.normcase(os.path.realpath(p))


def _under(p, root):
    try:
        return os.path.commonpath([p, root]) == root
    except ValueError:  # different drives
        return False


def workspace_root():
    """The repository holding the current directory (nearest ancestor with .git/.hg/.svn),
    else the current directory itself."""
    cwd = _norm(os.getcwd())
    d = cwd
    while True:
        if any(os.path.exists(os.path.join(d, m)) for m in (".git", ".hg", ".svn")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return cwd
        d = parent


def find_exe(name, skip=None, exact=False):
    """Look `name` up on PATH, absolute directories only, skipping the workspace (the
    repository around the current directory, or the current directory) and everything under
    it: shutil.which on Windows Python <= 3.11 searches the current directory first, and an
    activated project env puts workspace dirs on PATH. A file that resolves into the workspace
    through a link is skipped too. Best effort: run the probe from a directory you trust."""
    exts = [""]
    if IS_WIN and not exact:  # exact: only `name` itself (e.g. bash.exe, never a bash.cmd wrapper)
        exts = [e for e in os.environ.get("PATHEXT", ".EXE;.CMD;.BAT").split(";") if e]
        if os.path.splitext(name)[1]:
            exts = [""] + exts
    root = workspace_root()
    # If the workspace is home or a drive root (a dotfiles repo, or run from ~), "under it"
    # would cover user installs such as ~/.local/bin: only skip the directory itself.
    home = _norm(os.path.expanduser("~"))
    broad = _under(home, root)
    cwd = _norm(os.getcwd())
    cwd_tree = not _under(home, cwd)  # below home: the current subtree is still the workspace

    def inside(p):
        if not broad:
            return _under(p, root)
        return p == root or (cwd_tree and _under(p, cwd))
    for d in os.environ.get("PATH", "").split(os.pathsep):
        d = d.strip('"')
        if not d or not os.path.isabs(d) or inside(_norm(d)):
            continue
        for e in exts:
            f = os.path.join(d, name + e)
            if (os.path.isfile(f) and os.access(f, os.X_OK) and not inside(_norm(f))
                    and not (skip and skip(f))):
                return f
    return None


def win_bash():
    """Git Bash: the first native bash.exe on PATH, else a standard Git install. Never a WSL
    launcher (that starts a Linux VM)."""
    launchers = []  # the system launcher under every name it has (Sysnative for 32-bit Python)
    for d in (_try(system_dir), os.path.join(os.environ.get("SystemRoot") or os.environ.get("windir") or "",
                                              "Sysnative")):
        if d and os.path.isabs(d) and os.path.isfile(os.path.join(d, "bash.exe")):
            launchers.append(os.path.join(d, "bash.exe"))

    def wsl(f):  # System32\bash.exe and the WindowsApps alias both start WSL
        low = f.lower().replace("/", "\\")
        if any(s in low for s in ("\\system32\\", "\\sysnative\\", "\\syswow64\\", "\\windowsapps\\")):
            return True
        for l in launchers:
            try:
                if os.path.samefile(f, l):
                    return True
            except OSError:
                pass
        return False
    cands = [find_exe("bash.exe", skip=wsl, exact=True)]  # native only: a bash.cmd could forward to WSL  # the copy a harness running `bash` gets, if on PATH
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
                 os.environ.get("LOCALAPPDATA") and os.path.join(os.environ["LOCALAPPDATA"], "Programs")):
        if root and os.path.isabs(root):  # an unset variable must not become a relative path
            cands.append(os.path.join(root, "Git", "bin", "bash.exe"))
    for c in cands:
        if c and os.path.isfile(c) and not wsl(c):
            return c
    return None


def candidates(profiles=False):
    """(name, family, argv) for each shell found. argv runs an empty command. `profiles` adds
    login/profile launch modes, which run the user's startup scripts (and anything they start)."""
    out = []
    posix = [("bash", win_bash())] if IS_WIN else [(n, find_exe(n)) for n in ("bash", "zsh")]
    for name, p in posix:  # what agent shell tools run (not sh)
        if p:
            out.append((name, "posix", [p, "-c", "true"]))
            if profiles:
                out.append((name + " (login)", "posix-login", [p, "-lc", "true"]))
    # Windows PowerShell 5.1 only stands in when pwsh 7 is missing: agent tools run pwsh, and
    # 5.1 lacks `&&`, ternaries and UTF-8 defaults, so a faster 5.1 start is no reason to use it.
    pw = find_exe("pwsh")
    for name in ("pwsh", "powershell") if IS_WIN else ("pwsh",):
        p = find_exe(name)
        if p:
            fam = "powershell" if name == "pwsh" or not pw else "powershell-5"
            out.append((name, fam, [p, "-NoProfile", "-NonInteractive", "-Command", "exit"]))
            if profiles:
                out.append((name + " (profile)", fam + "-profile", [p, "-NonInteractive", "-Command", "exit"]))
    if IS_WIN:
        p = find_exe("cmd")
        if p:
            out.append(("cmd", "cmd", [p, "/d", "/c", "exit"]))
    return out


def _try(fn):
    try:
        return fn()
    except Exception:
        return None


def system_dir():
    """The real Windows system directory (GetSystemDirectoryW), not a guessed drive."""
    import ctypes
    buf = ctypes.create_unicode_buffer(260)
    n = ctypes.windll.kernel32.GetSystemDirectoryW(buf, 260)
    if not n or n >= 260:
        raise OSError("GetSystemDirectoryW failed")
    return buf.value


_DEFER = {"on": False, "pending": None}  # signals that arrive while a sample is being set up


def _exit_on_signal(signum, _frame):
    if _DEFER["on"]:  # no handle on the sample yet: act once its cleanup is in place
        _DEFER["pending"] = signum
        return
    raise SystemExit(128 + signum)


def _raise_pending():
    _DEFER["on"] = False
    s, _DEFER["pending"] = _DEFER["pending"], None
    if s:
        raise SystemExit(128 + s)


def run_once(argv, kw, limit=30):
    """Seconds until the shell exits, or None if it fails. Waits on the process itself
    (no timeout polling, which adds up to 50 ms on POSIX); a timer enforces `limit`."""
    kw = dict(kw)
    if IS_WIN:
        kw["creationflags"] = kw.get("creationflags", 0) | 0x00000200  # CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True  # own process group, so a timeout ends its children too
    _DEFER["on"] = True  # until the timer and the cleanup handler are in place
    try:
        t = time.perf_counter()
        p = subprocess.Popen(argv, **kw)
    except OSError:
        _raise_pending()
        return None

    def kill_tree():
        try:
            if IS_WIN:
                tk = os.path.join(system_dir(), "taskkill.exe")
                r = subprocess.run([tk, "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=10)
                if r.returncode == 0:
                    return
            else:
                os.killpg(p.pid, signal.SIGKILL)
                return
        except (OSError, subprocess.SubprocessError):
            pass
        try:  # tree kill failed: at least end the shell, so wait() returns
            p.kill()
        except OSError:
            pass
    killer = threading.Timer(limit, kill_tree)
    killer.start()
    try:
        _raise_pending()
        code = p.wait()
        dt = time.perf_counter() - t
    except BaseException:  # Ctrl+C: don't leave the sample's process group behind
        kill_tree()
        p.wait()
        raise
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
        fast, slow = (px[1], ps[1]) if diff > 0 else (ps[1], px[1])
        path = shells[fast].get("path")
        fast_s = fast + (" (%s)" % path if path else "")
        # Both wordings name the faster shell, so a gap near the threshold that lands on the
        # other side in a re-run changes the strength, never the direction.
        if abs(diff) < CLOSE_MS:
            r["recommendation"] = ("either: %s starts %d ms faster than %s, which is small; choose by task "
                                   "(POSIX tools vs cmdlets)" % (fast_s, abs(diff), slow))
        else:
            r["recommendation"] = ("prefer %s for general command-line work: %d ms faster to start per call "
                                   "than %s; keep %s for work only it can do" % (fast_s, abs(diff), slow, slow))
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


def measure(runs, profiles=False):
    shells, failed, inv = {}, [], {}
    for name, fam, argv in candidates(profiles):
        inv[name] = argv[0]  # every candidate's executable, measured or failed
        t = time_one(argv, runs)
        if t:
            shells[name] = dict(t, family=fam, path=argv[0])
        else:  # every launch mode, so a harness using login/profile can see it is unusable
            failed.append(name)
    if not any(v["family"] == "powershell" for v in shells.values()):  # pwsh failed: 5.1 stands in
        for v in shells.values():
            v["family"] = v["family"].replace("powershell-5", "powershell")
    res = {"v": CACHE_VERSION, "host": socket.gethostname(), "platform": sys.platform,
           "measured_at": int(time.time()), "runs": runs, "shells": shells,
           "inventory": inv}
    if failed:
        res["failed"] = failed
    res.update(recommend(shells))
    return res


def inventory(profiles=False):
    """Shell name -> executable for the shells this process would measure (no timing)."""
    return {name: argv[0] for name, _fam, argv in candidates(profiles)}


def valid_cache(c, runs, profiles=False):
    """A fresh, well-formed record for this host and platform, with derived fields recomputed."""
    if not (isinstance(c, dict) and c.get("v") == CACHE_VERSION and c.get("host") == socket.gethostname()
            and c.get("platform") == sys.platform and isinstance(c.get("measured_at"), (int, float))):
        return None
    shells = c.get("shells")
    if not isinstance(shells, dict) or not shells:  # never reuse a run that found nothing
        return None
    if not isinstance(c.get("runs"), int) or c["runs"] < runs:  # fewer samples than asked for
        return None
    for v in shells.values():
        if not (isinstance(v, dict) and isinstance(v.get("median_ms"), (int, float))
                and isinstance(v.get("p90_ms"), (int, float)) and isinstance(v.get("family"), str)):
            return None
    failed = c.get("failed", [])
    if not (isinstance(failed, list) and all(isinstance(f, str) for f in failed)):
        return None
    inv = c.get("inventory")
    if not isinstance(inv, dict) or set(inv) != set(shells) | set(failed):
        return None
    if inv != inventory(profiles) or any(inv[k] != v.get("path") for k, v in shells.items()):
        return None  # another PATH or install (failed shells included): re-measure
    for k in ("fastest_posix", "fastest_powershell", "recommendation", "profile_cost_ms", "login_cost_ms"):
        c.pop(k, None)
    c.update(recommend(shells))
    return c


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true", help="measure even if a fresh cached result exists")
    ap.add_argument("--max-age-days", type=float, default=7, help="reuse a cached result up to this old (7)")
    ap.add_argument("--runs", type=int, default=5, help="timed runs per shell (5)")
    ap.add_argument("--profiles", action="store_true",
                    help="also time login shells and PowerShell with profile; runs your startup "
                         "scripts runs+1 times each, including anything they start")
    a = ap.parse_args(argv)
    if threading.current_thread() is threading.main_thread():
        # A harness that cancels with SIGTERM/SIGHUP would otherwise end Python without
        # unwinding, leaving the sample (in its own session) running: exit through run_once's
        # cleanup instead.
        for sig in ("SIGINT", "SIGTERM", "SIGHUP"):
            if hasattr(signal, sig):
                try:
                    signal.signal(getattr(signal, sig), _exit_on_signal)
                except (OSError, ValueError):
                    pass
    path = cache_path()
    if not a.force:
        try:
            with open(path, encoding="utf-8") as f:
                c = json.load(f)
            c = valid_cache(c, max(1, a.runs), a.profiles)
            if c and time.time() - c["measured_at"] < a.max_age_days * 86400:
                c["cached"] = True
                print(json.dumps(c))
                return 0
        except (OSError, ValueError):
            pass
    res = measure(max(1, a.runs), a.profiles)
    try:
        if not res["shells"]:  # a run that found nothing (restricted PATH, blocked launches) isn't cached
            raise OSError("no shell measured")
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        d = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(prefix=".shell-probe-", suffix=".tmp", dir=d)
        try:  # publish atomically: concurrent readers see the old record or the new one, never half
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(res, f)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as e:
        sys.stderr.write("warning: not cached (%s): %s\n" % (path, e))
    res["cached"] = False
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
