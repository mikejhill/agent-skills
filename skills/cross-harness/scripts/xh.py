#!/usr/bin/env python3
"""cross-harness: run a review or task in another agent CLI (Claude Code or Codex).

Every job is one short-lived CLI process (`codex exec` / `claude -p`) owned by a
small supervisor. There is no daemon, no shared server, and no hook. The
supervisor:

- runs with its working directory in the state home, never in the user's repo;
- contains the job's whole process tree (Windows Job Object with
  KILL_ON_JOB_CLOSE; POSIX process group, plus PR_SET_PDEATHSIG on Linux);
- ends the tree when the job finishes, is cancelled, exceeds its time limit, or
  its owner (the calling Claude Code / Codex process) exits;
- records state per job (owner pid, target dir, pids with start times), so any
  invocation from any directory can list, cancel, or sweep jobs.

Python 3.8+, standard library only.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

IS_WIN = os.name == "nt"
SKILL_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_DIR / "assets" / "prompts"
DEPTH_ENV = "CROSS_HARNESS_DEPTH"
HOME_ENV = "CROSS_HARNESS_HOME"
TARGETS = ("codex", "claude")
ACTIVE = ("starting", "running")
EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_RUNNING = 0, 1, 2, 3

# Variables that tie a process to the calling session. The child is a separate
# session, so it must not inherit them.
SESSION_ENV_VARS = (
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SSE_PORT",
    "CLAUDE_ENV_FILE",
    "CLAUDE_CODE_SESSION_ID",
    "CODEX_SANDBOX",
    "CODEX_SANDBOX_NETWORK_DISABLED",
    "CODEX_THREAD_ID",
)

# Read-only tool set for Claude Code reviews and read-only tasks.
CLAUDE_READ_TOOLS = [
    "Read", "Grep", "Glob", "LS",
    "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)", "Bash(git status:*)",
    "Bash(git blame:*)", "Bash(git ls-files:*)", "Bash(git merge-base:*)",
    "Bash(git rev-parse:*)", "Bash(git branch:*)",
]
CLAUDE_WRITE_DENY = ["Edit", "Write", "MultiEdit", "NotebookEdit"]


# --------------------------------------------------------------------------- utils


class XhError(Exception):
    def __init__(self, msg: str, code: int = EXIT_FAIL):
        super().__init__(msg)
        self.code = code


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(s: str) -> float:
    try:
        return _dt.datetime.fromisoformat(s).timestamp()
    except (TypeError, ValueError):
        return 0.0


def state_home() -> Path:
    env = os.environ.get(HOME_ENV)
    if env:
        return Path(env).expanduser()
    if IS_WIN:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "cross-harness"
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "cross-harness"


_JOBS_DIR = None


def jobs_dir() -> Path:
    global _JOBS_DIR
    if _JOBS_DIR is not None:
        return _JOBS_DIR
    d = state_home() / "jobs"
    try:
        d.mkdir(parents=True, exist_ok=True)
        # Per-process probe name: concurrent xh.py processes must not delete
        # each other's probe.
        probe = d / f".write-probe-{os.getpid()}-{secrets.token_hex(3)}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as e:
        raise XhError(
            f"cannot write the state home {d} ({e.strerror or e}). If you are inside a "
            "sandbox (for example Codex workspace-write), rerun this command with "
            f"escalated permissions, or set {HOME_ENV} to a writable directory."
        )
    _JOBS_DIR = d
    return d


def atomic_write_json(path: Path, data: dict) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(3)}.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    for attempt in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:  # Windows: a reader holds the file briefly
            if attempt == 19:
                raise
            time.sleep(0.05)


def load_job(job_id: str) -> dict:
    p = jobs_dir() / job_id / "job.json"
    if not p.is_file():
        # Accept a unique prefix.
        matches = [d.name for d in jobs_dir().iterdir() if d.name.startswith(job_id)]
        if len(matches) == 1:
            p = jobs_dir() / matches[0] / "job.json"
        elif len(matches) > 1:
            raise XhError(f"job id '{job_id}' is ambiguous: {', '.join(sorted(matches))}", EXIT_USAGE)
        else:
            raise XhError(f"no job '{job_id}'. List jobs with: xh.py status --all", EXIT_USAGE)
    for _ in range(10):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, PermissionError):
            time.sleep(0.05)
    return json.loads(p.read_text(encoding="utf-8"))


def save_job(job: dict) -> None:
    job["updated"] = now_iso()
    atomic_write_json(jobs_dir() / job["id"] / "job.json", job)


def update_job(job_id: str, **fields) -> dict:
    job = load_job(job_id)
    job.update(fields)
    save_job(job)
    return job


def all_jobs() -> list:
    out = []
    for d in sorted(jobs_dir().iterdir()):
        p = d / "job.json"
        if p.is_file():
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    return out


def emit(obj, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2))
    elif isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, indent=2))


# ---------------------------------------------------------------- process identity

if IS_WIN:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_TERMINATE = 0x0001
    STILL_ACTIVE = 259
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    _k32.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    _k32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    _k32.Process32FirstW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))
    _k32.Process32NextW.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W))


def proc_start_time(pid: int):
    """Opaque start-time token for pid, or None if it is not running."""
    if not pid or pid <= 0:
        return None
    if IS_WIN:
        h = _k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return None
        try:
            code = wintypes.DWORD()
            if not _k32.GetExitCodeProcess(h, ctypes.byref(code)) or code.value != STILL_ACTIVE:
                return None
            c, e, k, u = (wintypes.FILETIME() for _ in range(4))
            if not _k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
                return None
            return str((c.dwHighDateTime << 32) | c.dwLowDateTime)
        finally:
            _k32.CloseHandle(h)
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            raw = stat.read_text()
            fields = raw[raw.rindex(")") + 2:].split()
            if fields[0] == "Z":
                return None
            return fields[19]
        except (OSError, ValueError, IndexError):
            return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        pass
    try:
        out = subprocess.run(["ps", "-o", "lstart=,stat=", "-p", str(pid)],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if not out or out.split()[-1].startswith("Z"):
        return None
    return " ".join(out.split()[:-1])


def alive(pid, start) -> bool:
    """True if pid runs and is the same process that was recorded."""
    cur = proc_start_time(pid) if pid else None
    if cur is None:
        return False
    return start in (None, "unknown") or cur == "unknown" or cur == start


def process_table():
    """{pid: (ppid, name)} for owner detection and diagnostics."""
    table = {}
    if IS_WIN:
        snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
        if snap in (None, wintypes.HANDLE(-1).value):
            return table
        try:
            e = PROCESSENTRY32W()
            e.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            ok = _k32.Process32FirstW(snap, ctypes.byref(e))
            while ok:
                table[e.th32ProcessID] = (e.th32ParentProcessID, e.szExeFile)
                ok = _k32.Process32NextW(snap, ctypes.byref(e))
        finally:
            _k32.CloseHandle(snap)
        return table
    if Path("/proc").is_dir():
        for d in Path("/proc").iterdir():
            if not d.name.isdigit():
                continue
            try:
                raw = (d / "stat").read_text()
                name = raw[raw.index("(") + 1:raw.rindex(")")]
                ppid = int(raw[raw.rindex(")") + 2:].split()[1])
                table[int(d.name)] = (ppid, name)
            except (OSError, ValueError, IndexError):
                continue
        return table
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,comm="],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3:
                table[int(parts[0])] = (int(parts[1]), parts[2])
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return table


def detect_owner():
    """Nearest ancestor that is a Claude Code or Codex process, else None."""
    table = process_table()
    pid, seen = os.getppid(), set()
    while pid and pid not in seen and pid in table:
        seen.add(pid)
        ppid, name = table[pid]
        base = os.path.basename(name).lower()
        if base.endswith(".exe"):
            base = base[:-4]
        if base in ("claude", "codex"):
            return {"pid": pid, "start": proc_start_time(pid), "name": base}
        pid = ppid
    return None


def kill_tree(pid: int, start) -> bool:
    """Best-effort kill of a recorded process tree (used by sweep and cancel)."""
    if not alive(pid, start):
        return False
    if IS_WIN:
        table = process_table()
        victims, frontier = [], [pid]
        while frontier:
            p = frontier.pop()
            victims.append(p)
            frontier.extend(c for c, (pp, _) in table.items() if pp == p and c not in victims)
        for p in reversed(victims):
            h = _k32.OpenProcess(PROCESS_TERMINATE, False, p)
            if h:
                _k32.TerminateProcess(h, 1)
                _k32.CloseHandle(h)
        return True
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return False
    for _ in range(50):
        if not alive(pid, start):
            break
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        pass
    return True


def kill_group(pgid) -> bool:
    """POSIX: end what is left of a job's process group."""
    if not pgid:
        return False
    try:
        os.killpg(pgid, signal.SIGKILL)
        return True
    except OSError:
        return False


def recent(job: dict) -> bool:
    """Guard against pid reuse: only act on groups of jobs that could still run."""
    limit = (job.get("timeout_min") or 30) * 60 + 3600
    return time.time() - parse_iso(job.get("created", "")) < limit


# -------------------------------------------------------------- binary resolution


def resolve_cli(target: str) -> list:
    """argv prefix that runs the target CLI directly, never through a shell."""
    override = os.environ.get(f"CROSS_HARNESS_{target.upper()}_BIN")
    found = override or shutil.which(target)
    if not found:
        raise XhError(f"'{target}' CLI not found on PATH. Install it or set CROSS_HARNESS_{target.upper()}_BIN.")
    path = Path(found)
    if not IS_WIN or path.suffix.lower() in (".exe", ""):
        if not IS_WIN and path.suffix.lower() in (".py",):
            return [sys.executable, str(path)]
        return [str(path)]
    # Windows npm shims (.cmd/.ps1/.bat): run the script they wrap with node
    # directly. Spawning a .cmd needs a shell, which hides the real process and
    # mangles arguments.
    if path.suffix.lower() == ".py":
        return [sys.executable, str(path)]
    native = _windows_native_exe(path, target)
    if native:
        return [str(native)]
    js = _shim_script(path)
    node = shutil.which("node")
    if js and node:
        return [node, str(js)]
    raise XhError(
        f"'{found}' is a script shim and its target could not be resolved. Set "
        f"CROSS_HARNESS_{target.upper()}_BIN to the real {target}.exe or entry script."
    )


def _windows_native_exe(shim: Path, target: str):
    if target != "codex":
        return None
    root = shim.parent / "node_modules" / "@openai" / "codex"
    for pattern in ("vendor/*/codex/codex.exe", "node_modules/@openai/codex-*/vendor/*/codex/codex.exe"):
        hits = sorted(root.glob(pattern))
        if hits:
            return hits[0]
    return None


def _shim_script(shim: Path):
    for candidate in (shim, shim.with_suffix(".cmd"), shim.with_suffix(".ps1")):
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r'(?:%~?dp0%?|\$basedir)[\\/]+([^"\s]+?\.(?:c?js|mjs))', text, re.I)
        if m:
            js = (shim.parent / m.group(1).replace("\\", os.sep)).resolve()
            if js.is_file():
                return js
    return None


# ------------------------------------------------------------------ command build


def load_prompt_template(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def scope_text(a) -> str:
    if a.commit:
        return f"the changes introduced by commit {a.commit} (`git show {a.commit}`)"
    if a.base:
        return (f"the changes on the current branch relative to `{a.base}`: run "
                f"`git diff {a.base}...HEAD` and `git log --oneline {a.base}..HEAD`, plus any "
                "uncommitted changes (`git status`, `git diff`, `git diff --cached`)")
    return ("the uncommitted changes in the working tree: staged, unstaged, and untracked "
            "files (`git status`, `git diff`, `git diff --cached`; read untracked files directly)")


def build_review_prompt(a) -> str:
    name = "adversarial-review.txt" if a.adversarial else "review.txt"
    focus = (a.focus or "").strip() or "No extra focus given. Review the whole change."
    return (load_prompt_template(name)
            .replace("{{SCOPE}}", scope_text(a))
            .replace("{{FOCUS}}", focus))


CLAUDE_NATIVE_TOOLS = ["Read", "Grep", "Glob", "LS", "Agent", "Task", "Bash", "WebFetch", "TodoWrite"]


def build_command(job: dict, step: str, prompt, out_path: Path) -> tuple:
    """Return (argv, stdin_text or None) for one step: 'review', 'fix' or 'task'."""
    t, kind = job["target"], job["kind"]
    argv = resolve_cli(t)
    model, effort = job.get("model"), job.get("effort")
    extra = job.get("extra") or []
    native = kind == "review" and step == "review" and job.get("mode") == "native"
    if step == "fix":
        sandbox = "workspace-write"
    elif native and t == "codex":
        sandbox = job.get("sandbox") or "inherit"
    else:
        sandbox = job.get("sandbox") or "read-only"
    ephemeral = job.get("ephemeral") and step != "fix"
    resume = job.get("resume_session") if step == "task" else None

    if t == "codex":
        common = ["--json", "-o", str(out_path)]
        if model:
            common += ["-m", model]
        if effort:
            common += ["-c", f'model_reasoning_effort="{effort}"']
        if job.get("isolate"):
            common += ["--ignore-rules"]
        if ephemeral:
            common += ["--ephemeral"]
        cfg_sb = [] if sandbox == "inherit" else ["-c", f'sandbox_mode="{sandbox}"']
        if native:
            scope = (["--commit", job["commit"]] if job.get("commit")
                     else ["--base", job["base"]] if job.get("base") else ["--uncommitted"])
            return argv + ["exec", "review"] + scope + cfg_sb + common + job.get("native_args", []) + extra, None
        if resume:
            return argv + ["exec", "resume", resume] + cfg_sb + common + extra + ["-"], prompt
        sb = [] if sandbox == "inherit" else ["-s", sandbox]
        return argv + ["exec"] + sb + common + extra + ["-"], prompt

    # claude
    args = ["-p", "--output-format", "json"]
    if model:
        args += ["--model", model]
    if effort:
        args += ["--effort", effort]
    if ephemeral:
        args += ["--no-session-persistence"]
    if job.get("isolate"):
        args += ["--setting-sources", "user"]
    if resume:
        args += ["--resume", resume]
    allow = job.get("allow_tools", [])
    if native:
        # The harness's own review command decides what it does; grant what it
        # needs. It edits only when asked to fix.
        args += ["--allowedTools", ",".join(CLAUDE_NATIVE_TOOLS + allow)]
        if job.get("fix"):
            args += ["--permission-mode", "acceptEdits"]
        else:
            args += ["--disallowedTools", ",".join(CLAUDE_WRITE_DENY)]
    elif sandbox == "read-only":
        args += ["--allowedTools", ",".join(CLAUDE_READ_TOOLS + allow)]
        args += ["--disallowedTools", ",".join(CLAUDE_WRITE_DENY)]
    elif sandbox == "workspace-write":
        args += ["--permission-mode", "acceptEdits"]
        tools = CLAUDE_NATIVE_TOOLS if step == "fix" else CLAUDE_READ_TOOLS
        args += ["--allowedTools", ",".join(tools + allow)]
    elif allow:
        args += ["--allowedTools", ",".join(allow)]
    return argv + args + extra, prompt


def claude_native_prompt(job: dict) -> str:
    """'/code-review ...' with the caller's arguments passed through verbatim."""
    cmd = os.environ.get("CROSS_HARNESS_CLAUDE_REVIEW_CMD", "/code-review")
    parts = [cmd] + list(job.get("native_args") or [])
    if job.get("fix") and "--fix" not in parts:
        parts.append("--fix")
    if job.get("post") and job.get("pr") and "--comment" not in parts:
        parts.append("--comment")
    target = job.get("pr") or job.get("branch_target")
    if target:
        parts.append(str(target))
    return " ".join(parts)


def fix_prompt(job: dict, review_text: str) -> str:
    return (load_prompt_template("fix.txt")
            .replace("{{SCOPE}}", job.get("scope_text") or "the reviewed changes")
            .replace("{{REVIEW}}", review_text.strip()))


# -------------------------------------------------------------------- review hosts


def _git(cwd, *args) -> str:
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else ""


def review_host(cwd) -> str:
    """'github' or 'gitlab' from the origin remote, or CROSS_HARNESS_REVIEW_HOST."""
    forced = os.environ.get("CROSS_HARNESS_REVIEW_HOST")
    if forced:
        return forced.lower()
    url = _git(cwd, "remote", "get-url", "origin").lower()
    if "gitlab" in url:
        return "gitlab"
    if "github" in url:
        return "github"
    raise XhError(f"cannot tell the review host from origin '{url or '(none)'}'. Set "
                  "CROSS_HARNESS_REVIEW_HOST=github or gitlab.", EXIT_USAGE)


def _host_cli(host: str) -> str:
    name = {"github": "gh", "gitlab": "glab"}.get(host)
    if not name:
        raise XhError(f"posting to '{host}' is not supported (github, gitlab)", EXIT_USAGE)
    exe = os.environ.get(f"CROSS_HARNESS_{name.upper()}_BIN") or shutil.which(name)
    if not exe:
        raise XhError(f"posting to {host} needs the '{name}' CLI, signed in", EXIT_USAGE)
    return [sys.executable, exe] if exe.lower().endswith(".py") else [exe]


def current_review_request(cwd) -> dict:
    """{'host','number','base'} for the PR/MR of the checked-out branch."""
    host = review_host(cwd)
    cli = _host_cli(host)
    if host == "github":
        r = subprocess.run([*cli, "pr", "view", "--json", "number,baseRefName"], cwd=str(cwd),
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            return {"host": host, "number": d["number"], "base": d.get("baseRefName")}
    else:
        r = subprocess.run([*cli, "mr", "view", "-F", "json"], cwd=str(cwd),
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            d = json.loads(r.stdout)
            return {"host": host, "number": d["iid"], "base": d.get("target_branch")}
    raise XhError(f"no open {'PR' if host == 'github' else 'MR'} found for the current branch; "
                  f"pass --pr N ({(r.stderr or r.stdout).strip()[:200]})", EXIT_USAGE)


def review_request(cwd, number) -> dict:
    host = review_host(cwd)
    cli = _host_cli(host)
    if host == "github":
        r = subprocess.run([*cli, "pr", "view", str(number), "--json", "number,baseRefName"], cwd=str(cwd),
                           capture_output=True, text=True, timeout=60)
        key_base = "baseRefName"
    else:
        r = subprocess.run([*cli, "mr", "view", str(number), "-F", "json"], cwd=str(cwd),
                           capture_output=True, text=True, timeout=60)
        key_base = "target_branch"
    if r.returncode != 0:
        raise XhError(f"cannot read {host} review request {number}: {(r.stderr or r.stdout).strip()[:300]}",
                      EXIT_USAGE)
    return {"host": host, "number": int(number), "base": json.loads(r.stdout).get(key_base)}


def post_review(job: dict, body: str) -> str:
    """Publish a review summary comment on the PR/MR. Returns the CLI's output."""
    cwd, host = job["cwd"], job["post_host"]
    cli = _host_cli(host)
    if host == "github":
        path = jobs_dir() / job["id"] / "post-body.md"
        path.write_text(body, encoding="utf-8")
        argv = [*cli, "pr", "comment", str(job["pr"]), "--body-file", str(path)]
    else:
        argv = [*cli, "mr", "note", str(job["pr"]), "--message", body]
    r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120,
                       env=child_env(job), stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise XhError(f"posting failed: {(r.stderr or r.stdout).strip()[:500]}")
    return (r.stdout or "posted").strip()


def child_env(job: dict) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in SESSION_ENV_VARS}
    env[DEPTH_ENV] = str(int(os.environ.get(DEPTH_ENV, "0") or 0) + 1)
    env["CROSS_HARNESS_JOB"] = job["id"]
    return env


# -------------------------------------------------------------------- containment


class Containment:
    """Holds the job's process tree and guarantees it ends with the supervisor."""

    def __init__(self):
        self.job_handle = None
        if IS_WIN:
            self._init_win_job()

    def _init_win_job(self):
        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class EXTENDED(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        _k32.CreateJobObjectW.restype = wintypes.HANDLE
        _k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        _k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
        _k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        _k32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        _k32.GetCurrentProcess.restype = wintypes.HANDLE
        h = _k32.CreateJobObjectW(None, None)
        if not h:
            raise XhError(f"CreateJobObject failed ({ctypes.get_last_error()})")
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _k32.SetInformationJobObject(h, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise XhError(f"SetInformationJobObject failed ({ctypes.get_last_error()})")
        # The supervisor joins the job itself, so every process it starts is
        # born inside it (no assign-after-spawn race). When the supervisor
        # exits for any reason, the last handle closes and Windows kills the
        # whole tree.
        if not _k32.AssignProcessToJobObject(h, _k32.GetCurrentProcess()):
            raise XhError(f"AssignProcessToJobObject failed ({ctypes.get_last_error()})")
        self.job_handle = h

    def popen_kwargs(self) -> dict:
        if IS_WIN:
            return {"creationflags": 0x08000000}  # CREATE_NO_WINDOW
        kw = {"start_new_session": True}
        if sys.platform.startswith("linux"):
            kw["preexec_fn"] = _linux_pdeathsig
        return kw

    def terminate(self, child):
        """End the child's whole tree. On Windows this also ends the supervisor."""
        if IS_WIN:
            _k32.TerminateJobObject(self.job_handle, 1)
            return
        if child is None:
            return
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except OSError:
            pass
        deadline = time.time() + 5
        while time.time() < deadline and child.poll() is None:
            time.sleep(0.1)
        self.reap(child)

    def reap(self, child):
        """Kill stragglers left in the tree after the main CLI exited."""
        if IS_WIN:
            _k32.TerminateJobObject(self.job_handle, 0)
            return
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except OSError:
            pass


def _linux_pdeathsig():
    try:
        import ctypes as _c
        _c.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG
    except Exception:  # noqa: BLE001 - best effort
        pass


# ---------------------------------------------------------------------- supervisor


def codex_output_path(job: dict, prefix: str, out_path: Path) -> tuple:
    """Where Codex writes its final message (-o): (path, scratch dir to remove or None).

    Codex 0.170+ opens the -o file with a strict no-follow open on Windows and has been
    seen to reject paths under %LOCALAPPDATA%\\cross-harness with "path contains a
    reparse point" although no component is a reparse point, while paths under
    %TEMP% work. So on Windows, Codex writes into a private temp dir and the result
    is moved into the job dir afterwards. Elsewhere it writes into the job dir.
    """
    if job["target"] != "codex" or not IS_WIN:
        return out_path, None
    try:
        root = scratch_root()
        root.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=f"{job['id']}-{prefix}-", dir=root))
    except OSError:
        return out_path, None
    return scratch / out_path.name, scratch


def scratch_root() -> Path:
    """The only place scratch dirs live; sweep reclaims leftovers by scanning it.

    Namespaced by state home, so a sweep under one CROSS_HARNESS_HOME never
    touches the scratch dirs of jobs that belong to another.
    """
    key = hashlib.sha256(str(jobs_dir().resolve()).lower().encode("utf-8")).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / "cross-harness-out" / key


SCRATCH_NAME = re.compile(r"^(xh-\d{8}-\d{6}-[0-9a-f]{4})-(result|fix)-[A-Za-z0-9_]+$")


def reclaim_scratch() -> None:
    """Remove scratch dirs whose job is finished or gone.

    A cancel, timeout or killed supervisor can end before its own cleanup. Only dirs
    directly in scratch_root() whose names match SCRATCH_NAME are touched, and none
    younger than a minute, so a starting or just-finished supervisor keeps its own.
    """
    try:
        entries = list(scratch_root().iterdir())
    except OSError:  # includes no usable temp dir at all
        return
    for d in entries:
        m = SCRATCH_NAME.match(d.name)
        if not m or d.is_symlink() or not d.is_dir():
            continue
        try:
            if time.time() - d.stat().st_mtime < 60:
                continue
        except OSError:
            continue
        p = jobs_dir() / m.group(1) / "job.json"
        try:
            status = json.loads(p.read_text(encoding="utf-8")).get("status") if p.is_file() else None
        except (OSError, json.JSONDecodeError):
            continue
        if status not in ACTIVE:
            shutil.rmtree(d, ignore_errors=True)


def collect_output(cli_out: Path, out_path: Path, scratch):
    """Move a final message written outside the job dir into it, then drop the scratch dir.

    The copy goes to a staging file that replaces the destination only once complete,
    so a failed copy never leaves a truncated result. Returns an error string or None.
    """
    if not scratch:
        return None
    err = None
    staging = out_path.with_name(out_path.name + ".partial")
    try:
        if cli_out.is_file():
            shutil.copyfile(cli_out, staging)
            os.replace(staging, out_path)
    except OSError as e:
        err = f"could not copy the final message into the job dir: {e}"
        try:
            staging.unlink()
        except OSError:
            pass
    shutil.rmtree(scratch, ignore_errors=True)
    return err


def parse_outputs(target: str, stdout_path: Path, out_path: Path, fallback_session=None) -> dict:
    """Read one CLI run's output files into result fields."""
    fields = {}
    if target == "codex":
        session, errors, last_message, final_message = None, [], None, None
        try:
            # Split on "\n" only: str.splitlines() also splits at U+2028/U+2029,
            # which are legal unescaped inside JSON strings.
            for line in stdout_path.read_text(encoding="utf-8", errors="replace").split("\n"):
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                typ = ev.get("type", "")
                if typ in ("thread.started", "session.created", "session_configured"):
                    session = ev.get("thread_id") or ev.get("session_id") or session
                elif typ == "item.completed" and (ev.get("item") or {}).get("type") == "agent_message":
                    last_message = ev["item"].get("text") or ""
                elif typ == "turn.completed":
                    final_message, last_message = last_message, None
                elif typ in ("error", "turn.failed"):
                    msg = ev.get("message") or (ev.get("error") or {}).get("message")
                    if msg:
                        errors.append(str(msg))
        except OSError:
            pass
        fields["session"] = session or fallback_session
        # Fallback when Codex completed a turn but did not write the -o file. Only the
        # last message of a completed turn counts; a trailing progress update does not.
        if final_message and not errors and not (out_path.is_file() and out_path.stat().st_size > 0):
            staging = out_path.with_name(out_path.name + ".partial")
            try:
                staging.write_bytes(final_message.encode("utf-8"))  # no newline translation
                os.replace(staging, out_path)
            except OSError as e:
                errors.append(f"could not write the recovered final message: {e}")
                try:
                    staging.unlink()
                except OSError:
                    pass
        if errors:
            fields["error"] = errors[-1]
    else:
        try:
            raw = stdout_path.read_text(encoding="utf-8", errors="replace").strip()
            data = json.loads(raw[raw.find("{"):]) if "{" in raw else {}
        except (OSError, json.JSONDecodeError):
            data = {}
        if data:
            fields["session"] = data.get("session_id")
            fields["cost_usd"] = data.get("total_cost_usd")
            text = data.get("result") or ""
            out_path.write_text(text, encoding="utf-8")
            if data.get("is_error"):
                fields["error"] = text[:500] or data.get("subtype")
    return fields


def progress(final: dict) -> dict:
    """Intermediate fields: never a terminal status while steps remain."""
    return {k: v for k, v in final.items() if k != "status"}


class Stop(Exception):
    """A watchdog condition ended the job."""

    def __init__(self, status, reason):
        super().__init__(reason)
        self.status, self.reason = status, reason


def supervise(job_id: str) -> int:
    jdir = jobs_dir() / job_id
    os.chdir(jdir)  # never hold the user's directory as our cwd
    job = update_job(job_id, supervisor={"pid": os.getpid(), "start": proc_start_time(os.getpid())})
    cont = Containment()
    state = {"child": None}
    deadline = time.time() + job["timeout_min"] * 60
    owner = job.get("owner")
    cancel_flag = jdir / "cancel"

    def handle_signal(signum, _frame):
        update_job(job_id, status="cancelled", ended=now_iso(), reason=f"signal {signum}")
        cont.terminate(state["child"])
        os._exit(EXIT_FAIL)

    for sig in ("SIGTERM", "SIGINT", "SIGHUP", "SIGBREAK"):
        if hasattr(signal, sig):
            try:
                signal.signal(getattr(signal, sig), handle_signal)
            except (OSError, ValueError):
                pass

    def check_stop():
        if cancel_flag.exists():
            raise Stop("cancelled", "cancelled by request")
        if time.time() > deadline:
            raise Stop("timed_out", f"time limit of {job['timeout_min']} min reached")
        if owner and not alive(owner["pid"], owner.get("start")):
            raise Stop("orphaned", f"owner {owner['name']} (pid {owner['pid']}) exited")

    def run_step(step: str, prompt, prefix: str) -> dict:
        """Run one CLI step to completion. Returns parsed fields plus exit_code."""
        out_path, so_path, se_path = jdir / f"{prefix}.md", jdir / f"{prefix}.stdout.log", jdir / f"{prefix}.stderr.log"
        cli_out, scratch = codex_output_path(job, prefix, out_path)
        try:
            fields = _run_step(step, prompt, out_path, so_path, se_path, cli_out)
        except BaseException:
            if scratch:
                shutil.rmtree(scratch, ignore_errors=True)
            raise
        copy_err = collect_output(cli_out, out_path, scratch)
        fields.update(parse_outputs(job["target"], so_path, out_path, job.get("resume_session")))
        has = out_path.is_file() and out_path.stat().st_size > 0
        if copy_err and not has:
            fields["error"] = copy_err
        fields["ok"] = fields["exit_code"] == 0 and has and not fields.get("error")
        if not fields["ok"] and not fields.get("error"):
            tail = se_path.read_text(encoding="utf-8", errors="replace")[-800:].strip()
            fields["error"] = tail or f"exit code {fields['exit_code']}" + ("" if has else ", no final message")
        return fields

    def _run_step(step, prompt, out_path, so_path, se_path, cli_out) -> dict:
        argv, stdin_text = build_command(job, step, prompt, cli_out)
        with open(so_path, "wb") as so, open(se_path, "wb") as se:
            child = subprocess.Popen(
                argv, cwd=job["cwd"], env=child_env(job),
                stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
                stdout=so, stderr=se, **cont.popen_kwargs(),
            )
            state["child"] = child
            update_job(job_id, status="running", step=step,
                       argv=argv if step != "fix" else load_job(job_id).get("argv"),
                       **({"fix_argv": argv} if step == "fix" else {}),
                       child={"pid": child.pid, "start": proc_start_time(child.pid)})
            if stdin_text is not None:
                try:
                    child.stdin.write(stdin_text.encode("utf-8"))
                    child.stdin.close()
                except OSError:
                    pass
            try:
                while child.poll() is None:
                    time.sleep(1)
                    check_stop()
            except Stop as e:
                # Record first: on Windows, terminating the job ends this process too.
                update_job(job_id, status=e.status, reason=e.reason, ended=now_iso())
                cont.terminate(child)
                raise
        if not IS_WIN:
            cont.reap(child)  # end stragglers between steps (Windows: at job end)
        return {"exit_code": child.returncode}

    final = {}
    claude_native = job["target"] == "claude" and job.get("mode") == "native"
    try:
        main_step = "task" if job["kind"] == "task" else "review"
        prompt = (jdir / "prompt.txt").read_text(encoding="utf-8") if (jdir / "prompt.txt").exists() else None
        r = run_step(main_step, prompt, "result")
        ok = r.pop("ok")
        final.update(r)
        final["status"] = "succeeded" if ok else "failed"
        review_text = (jdir / "result.md").read_text(encoding="utf-8", errors="replace") if ok else ""
        if ok and job.get("fix") and not claude_native:
            update_job(job_id, **progress(final))
            fr = run_step("fix", fix_prompt(job, review_text), "fix")
            final["fix_status"] = "succeeded" if fr.pop("ok") else "failed"
            final["fix_session"] = fr.get("session")
            if final["fix_status"] == "failed":
                final["status"], final["error"] = "failed", f"fix step: {fr.get('error')}"
        if ok and job.get("post") and not claude_native:
            update_job(job_id, **progress(final))
            check_stop()
            body = f"**{job['target'].capitalize()} review** (cross-harness" + \
                   (", adversarial" if job.get("adversarial") else "") + ")\n\n" + review_text.strip()
            fix_md = jdir / "fix.md"
            if final.get("fix_status") == "succeeded" and fix_md.is_file():
                body += "\n\n---\n\n**Fixes applied**\n\n" + fix_md.read_text(encoding="utf-8").strip()
            try:
                final["posted"] = post_review(job, body)
            except XhError as e:
                final["status"], final["error"] = "failed", str(e)
    except Stop as e:
        final.update(status=e.status, reason=e.reason)
    except XhError as e:
        final.update(status="failed", error=str(e))
    except Exception as e:  # noqa: BLE001 - record any failure instead of leaving "running"
        final.update(status="failed", error=f"supervisor error: {e!r}")
    err = str(final.get("error") or "")
    if final.get("status") == "failed" and re.search(
            r"model_not_found|model is not supported|unknown model|invalid model", err, re.I):
        final["hint"] = ("the model was rejected; the target's configured default may not be available to this "
                         "account. Retry with --model set to a supported model.")
    final["ended"] = now_iso()
    final.pop("ok", None)
    update_job(job_id, **final)
    if state["child"] is not None or IS_WIN:
        cont.reap(state["child"])  # on Windows this ends the supervisor too
    return EXIT_OK


def spawn_supervisor(job_id: str) -> int:
    jdir = jobs_dir() / job_id
    argv = [sys.executable, str(Path(__file__).resolve()), "_supervise", job_id]
    kw = {"cwd": str(jdir), "stdin": subprocess.DEVNULL,
          "stdout": open(jdir / "supervisor.log", "ab"), "stderr": subprocess.STDOUT}
    if IS_WIN:
        pyw = Path(sys.executable).with_name("pythonw.exe")
        if pyw.is_file():
            argv[0] = str(pyw)
        base = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
        try:  # leave the caller's job object so the tool call ending does not kill us
            p = subprocess.Popen(argv, creationflags=base | 0x01000000, **kw)
        except OSError:
            p = subprocess.Popen(argv, creationflags=base, **kw)
    else:
        p = subprocess.Popen(argv, start_new_session=True, **kw)
    return p.pid


# --------------------------------------------------------------------------- sweep


def sweep(kill: bool = True) -> list:
    """Mark jobs whose supervisor vanished as lost and end leftover trees."""
    changed = []
    for job in all_jobs():
        if job.get("status") not in ACTIVE:
            continue
        sup = job.get("supervisor") or {}
        if sup and alive(sup.get("pid"), sup.get("start")):
            continue
        if not sup and time.time() - parse_iso(job.get("created", "")) < 30:
            continue  # still starting
        # The supervisor is gone. Re-read: it writes its final state before it
        # exits, so a record read before that write is stale.
        job = load_job(job["id"])
        if job.get("status") not in ACTIVE:
            continue
        killed = False
        ch = job.get("child") or {}
        if kill and ch:
            killed = kill_tree(ch.get("pid"), ch.get("start"))
            if not IS_WIN and not killed and recent(job):
                # The group leader may be gone (Linux parent-death signal) while
                # members it started remain. The group id is the leader's pid.
                killed = kill_group(ch.get("pid"))
        update_job(job["id"], status="lost", ended=now_iso(),
                   reason="supervisor exited without finishing" + ("; ended leftover processes" if killed else ""))
        changed.append(job["id"])
    reclaim_scratch()
    return changed


# ------------------------------------------------------------------------ commands


def new_job_id() -> str:
    return _dt.datetime.now().strftime("xh-%Y%m%d-%H%M%S-") + secrets.token_hex(2)


def resolve_session(target: str, value: str) -> str:
    if value and value.startswith("xh-"):
        prev = load_job(value)
        if prev["target"] != target:
            raise XhError(f"job {value} ran {prev['target']}, not {target}", EXIT_USAGE)
        if prev.get("kind") == "review" or prev.get("ephemeral") or not prev.get("session"):
            raise XhError(f"job {value} has no resumable session (reviews are ephemeral)", EXIT_USAGE)
        return prev["session"]
    return value


def create_job(a, kind: str, prompt) -> dict:
    depth = int(os.environ.get(DEPTH_ENV, "0") or 0)
    if depth >= 1 and not a.allow_nested:
        raise XhError(
            "this session was itself started by cross-harness. Nested hand-offs are refused "
            "to prevent loops; pass --allow-nested only if the user asked for it.", EXIT_USAGE)
    cwd = Path(a.cwd or os.getcwd()).resolve()
    if not cwd.is_dir():
        raise XhError(f"--cwd {cwd} is not a directory", EXIT_USAGE)
    resolve_cli(a.target)  # fail fast if missing
    sweep()
    job_id = new_job_id()
    jdir = jobs_dir() / job_id
    jdir.mkdir()
    owner = None if a.no_owner else detect_owner()
    job = {
        "id": job_id, "kind": kind, "target": a.target, "cwd": str(cwd),
        "label": a.label, "created": now_iso(), "status": "starting",
        "timeout_min": a.timeout, "owner": owner, "model": a.model, "effort": a.effort,
        "sandbox": a.sandbox, "isolate": a.isolate, "extra": a.extra or [],
        "allow_tools": [t for s in (a.allow_tools or []) for t in s.split(",") if t],
    }
    if kind == "review":
        job.update(base=a.base, commit=a.commit, focus=a.focus, adversarial=a.adversarial,
                   ephemeral=True, mode=a.mode, native_args=a.native_args, fix=a.fix,
                   post=a.post, pr=a.pr, post_host=a.post_host, scope_text=scope_text(a),
                   branch_target=a.branch_target)
    else:
        job.update(ephemeral=a.ephemeral,
                   resume_session=resolve_session(a.target, a.resume) if a.resume else None)
    if prompt is not None:
        (jdir / "prompt.txt").write_text(prompt, encoding="utf-8")
    save_job(job)
    # From here on only the supervisor writes job.json (it records its own pid
    # first), and the sweep writes only once the supervisor is gone. A single
    # writer avoids lost updates between processes.
    spawn_supervisor(job_id)
    return job


def read_prompt(a) -> str:
    if a.prompt_file:
        return Path(a.prompt_file).read_text(encoding="utf-8")
    if a.prompt and a.prompt != ["-"]:
        return " ".join(a.prompt)
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            return data
    raise XhError("no prompt: pass it as an argument, with --prompt-file, or on stdin", EXIT_USAGE)


def cmd_review(a) -> int:
    import shlex
    cwd = Path(a.cwd or os.getcwd()).resolve()
    a.native_args = shlex.split(a.native_args or "", posix=not IS_WIN) if a.native_args else []
    a.post_host, a.branch_target = None, None
    # Resolve the PR/MR first: it supplies the base and the post target.
    if a.pr is not None or a.post:
        req = review_request(cwd, a.pr) if a.pr is not None else current_review_request(cwd)
        a.pr, a.post_host = req["number"], req["host"]
        if not (a.base or a.commit or a.uncommitted) and req.get("base"):
            remote = f"origin/{req['base']}"
            a.base = remote if _git(cwd, "rev-parse", "--verify", "-q", remote) else req["base"]
    # Native review = the harness's own reviewer (Codex: exec review; Claude:
    # /code-review). Custom instructions need the skill's prompt instead.
    native = not (a.focus or a.adversarial or a.no_native)
    if native and a.target == "claude" and a.commit:
        native = False  # /code-review has no commit target
    if a.native_args and not native:
        raise XhError("--native-args applies only to native reviews (no --focus, --adversarial, --no-native)",
                      EXIT_USAGE)
    a.mode = "native" if native else "prompt"
    if native and a.target == "claude" and a.base and a.pr is None:
        a.branch_target = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD") or None
    if not native:
        prompt = build_review_prompt(a)
    elif a.target == "claude":
        prompt = claude_native_prompt({"native_args": a.native_args, "fix": a.fix, "post": a.post,
                                       "pr": a.pr, "branch_target": a.branch_target})
    else:
        prompt = None  # codex exec review takes its scope as flags
    job = create_job(a, "review", prompt)
    return after_start(job, a)


def cmd_task(a) -> int:
    a.sandbox = a.sandbox or ("workspace-write" if a.write else "read-only")
    job = create_job(a, "task", read_prompt(a))
    return after_start(job, a)


def after_start(job: dict, a) -> int:
    if a.wait:
        return do_wait(job["id"], a.wait, a.json)
    emit({"job": job["id"], "status": job["status"], "target": job["target"], "kind": job["kind"],
          "owner": job.get("owner"), "next": f"xh.py wait {job['id']} --timeout 90"}, True)
    return EXIT_OK


def render_result(job: dict, as_json: bool) -> str:
    jdir = jobs_dir() / job["id"]
    text = ""
    rp = jdir / "result.md"
    if rp.is_file():
        text = rp.read_text(encoding="utf-8", errors="replace")
    if as_json:
        return json.dumps({**summary(job), "result": text}, indent=2)
    head = f"[{job['id']}] {job['target']} {job['kind']}: {job['status']}"
    if job.get("session"):
        head += f" (session {job['session']})"
    if job.get("error") and job["status"] != "succeeded":
        head += f"\nerror: {job['error']}"
    if job.get("reason"):
        head += f"\nreason: {job['reason']}"
    if job.get("hint"):
        head += f"\nhint: {job['hint']}"
    if job.get("fix_status"):
        head += f"\nfix: {job['fix_status']} (details: xh.py result {job['id']} --fix-report)"
    if job.get("posted"):
        head += f"\nposted: {job['posted']}"
    return head + ("\n\n" + text.strip() if text.strip() else "")


def do_wait(job_id: str, timeout: float, as_json: bool) -> int:
    deadline = time.time() + max(1.0, timeout)
    while True:
        sweep()
        job = load_job(job_id)
        if job["status"] not in ACTIVE:
            print(render_result(job, as_json))
            return EXIT_OK if job["status"] == "succeeded" else EXIT_FAIL
        if time.time() >= deadline:
            emit({"job": job["id"], "status": job["status"], "elapsed_s": int(time.time() - parse_iso(job["created"])),
                  "next": f"xh.py wait {job['id']} --timeout {int(timeout)}"}, True)
            return EXIT_RUNNING
        time.sleep(1)


def cmd_wait(a) -> int:
    return do_wait(a.job, a.timeout, a.json)


def cmd_result(a) -> int:
    sweep()
    job = load_job(a.job)
    if a.fix_report:
        fp = jobs_dir() / job["id"] / "fix.md"
        print(fp.read_text(encoding="utf-8", errors="replace") if fp.is_file() else "no fix report")
        return EXIT_OK
    print(render_result(job, a.json))
    if job["status"] in ACTIVE:
        return EXIT_RUNNING
    return EXIT_OK if job["status"] == "succeeded" else EXIT_FAIL


def summary(job: dict) -> dict:
    keys = ("id", "target", "kind", "status", "label", "cwd", "created", "ended", "session",
            "exit_code", "error", "reason", "hint", "cost_usd", "mode", "pr", "fix_status", "posted")
    out = {k: job.get(k) for k in keys if job.get(k) is not None}
    if job.get("owner"):
        o = job["owner"]
        out["owner"] = f"{o['name']}:{o['pid']}" + ("" if alive(o["pid"], o.get("start")) else " (gone)")
    for k in ("supervisor", "child"):
        p = job.get(k) or {}
        if p.get("pid"):
            out[f"{k}_pid"] = p["pid"]
            out[f"{k}_alive"] = alive(p["pid"], p.get("start"))
    return out


def cmd_status(a) -> int:
    swept = sweep()
    if a.job:
        emit(summary(load_job(a.job)), True)
        return EXIT_OK
    jobs = [j for j in all_jobs() if a.all or j.get("status") in ACTIVE]
    rows = [summary(j) for j in jobs]
    if a.json:
        emit({"jobs": rows, "swept": swept, "state_home": str(state_home())}, True)
        return EXIT_OK
    if not rows:
        print("no active jobs" + ("" if a.all else " (use --all for finished ones)"))
    for r in rows:
        age = int(time.time() - parse_iso(r.get("created", "")))
        print(f"{r['id']}  {r['target']:6} {r['kind']:6} {r['status']:10} {age//60:>4}m  "
              f"owner={r.get('owner', '-')}  {r.get('cwd', '')}")
    if swept:
        print(f"swept: {', '.join(swept)}")
    return EXIT_OK


def cmd_cancel(a) -> int:
    targets = [j for j in all_jobs() if j.get("status") in ACTIVE] if a.all else [load_job(a.job)]
    if not targets:
        print("no active jobs")
    for job in targets:
        if job["status"] not in ACTIVE:
            print(f"{job['id']}: already {job['status']}")
            continue
        (jobs_dir() / job["id"] / "cancel").write_text(now_iso(), encoding="utf-8")
        sup = job.get("supervisor") or {}
        for _ in range(100):
            if not alive(sup.get("pid"), sup.get("start")):
                break
            time.sleep(0.1)
        else:
            # Supervisor did not react: end its tree directly.
            kill_tree(sup.get("pid"), sup.get("start"))
        sweep()
        print(f"{job['id']}: {load_job(job['id'])['status']}")
    return EXIT_OK


def cmd_cleanup(a) -> int:
    report = {"swept": [], "pruned": [], "stale_running": []}
    if not a.dry_run:
        report["swept"] = sweep()
    cutoff = time.time() - a.prune_days * 86400
    for job in all_jobs():
        if job.get("status") in ACTIVE:
            o = job.get("owner")
            if o and not alive(o["pid"], o.get("start")):
                report["stale_running"].append(job["id"])
            continue
        if parse_iso(job.get("ended") or job.get("created", "")) < cutoff:
            report["pruned"].append(job["id"])
            if not a.dry_run:
                shutil.rmtree(jobs_dir() / job["id"], ignore_errors=True)
    emit(report, True)
    return EXIT_OK


def cmd_check(a) -> int:
    out = {"state_home": str(state_home()), "nesting_depth": int(os.environ.get(DEPTH_ENV, "0") or 0),
           "caller": detect_owner(), "targets": {}}
    for t in ([a.target] if a.target else TARGETS):
        info = {}
        try:
            argv = resolve_cli(t)
            info["argv"] = argv
            r = subprocess.run(argv + ["--version"], capture_output=True, text=True, timeout=30,
                               stdin=subprocess.DEVNULL, env=child_env({"id": "check"}))
            info["version"] = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else None
            auth = ["login", "status"] if t == "codex" else ["auth", "status"]
            r = subprocess.run(argv + auth, capture_output=True, text=True, timeout=30,
                               stdin=subprocess.DEVNULL, env=child_env({"id": "check"}))
            info["auth"] = {"exit_code": r.returncode, "output": (r.stdout + r.stderr).strip()[:300]}
        except (XhError, OSError, subprocess.SubprocessError) as e:
            info["error"] = str(e)
        out["targets"][t] = info
    try:
        jobs_dir()
        out["state_writable"] = True
    except XhError as e:
        out["state_writable"] = False
        out["state_error"] = str(e)
    emit(out, True)
    return EXIT_OK


# ---------------------------------------------------------------------------- CLI


def add_job_opts(p):
    p.add_argument("--target", "-t", required=True, choices=TARGETS, help="agent CLI to run")
    p.add_argument("--cwd", help="repository/directory the job works in (default: current)")
    p.add_argument("--model", "-m", help="model passed through unchanged")
    p.add_argument("--effort", help="reasoning effort passed through unchanged")
    p.add_argument("--timeout", type=float, default=30, help="hard limit for the job in minutes (default 30)")
    p.add_argument("--wait", type=float, default=0, metavar="SECS",
                   help="block up to SECS for the result (exit 3 if still running)")
    p.add_argument("--isolate", action="store_true",
                   help="ignore the target repo's own agent config where the CLI allows it")
    p.add_argument("--allow-tools", action="append", metavar="LIST",
                   help="claude: extra allowed tools, comma-separated (e.g. 'Bash')")
    p.add_argument("--extra", action="append", metavar="ARG", help="extra raw CLI argument (repeatable)")
    p.add_argument("--label", help="free-text label shown in status")
    p.add_argument("--no-owner", action="store_true",
                   help="let the job outlive the calling session (still bounded by --timeout)")
    p.add_argument("--allow-nested", action="store_true", help="permit a hand-off from a handed-off session")
    p.add_argument("--json", action="store_true")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="xh.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check", help="find the CLIs, versions, auth, and state home")
    p.add_argument("--target", "-t", choices=TARGETS)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("review", help="start a read-only review in the other agent")
    add_job_opts(p)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--base", help="review the branch against this base ref")
    g.add_argument("--commit", help="review one commit")
    g.add_argument("--uncommitted", action="store_true", help="review working-tree changes (default)")
    p.add_argument("--pr", type=int, help="PR/MR number: sets the base and the post target")
    p.add_argument("--native-args", metavar="ARGS",
                   help="arguments passed verbatim to the native reviewer (Claude: '/code-review ARGS')")
    p.add_argument("--no-native", action="store_true", help="use the skill's review prompt instead")
    p.add_argument("--focus", help="extra review instructions (uses the skill's prompt)")
    p.add_argument("--adversarial", action="store_true", help="adversarial review (uses the skill's prompt)")
    p.add_argument("--fix", action="store_true", help="apply fixes for the findings in --cwd")
    p.add_argument("--post", action="store_true", help="post the review to the PR/MR (gh or glab)")
    p.add_argument("--sandbox", choices=("read-only", "workspace-write", "inherit"),
                   help="review sandbox (Codex native default: inherit; prompt reviews: read-only)")
    p.set_defaults(fn=cmd_review)

    p = sub.add_parser("task", help="hand a prompt or task to the other agent")
    add_job_opts(p)
    p.add_argument("prompt", nargs="*", help="prompt text, or '-' / stdin")
    p.add_argument("--prompt-file", help="read the prompt from a file")
    p.add_argument("--write", action="store_true", help="allow edits in --cwd (default read-only)")
    p.add_argument("--sandbox", choices=("read-only", "workspace-write", "inherit"),
                   help="explicit sandbox; 'inherit' uses the target's own config")
    p.add_argument("--resume", metavar="JOB_OR_SESSION", help="continue an earlier task's session")
    p.add_argument("--ephemeral", action="store_true", help="do not persist the session")
    p.set_defaults(fn=cmd_task)

    p = sub.add_parser("wait", help="wait for a job; exit 0 done, 1 failed, 3 still running")
    p.add_argument("job")
    p.add_argument("--timeout", type=float, default=90, help="seconds (default 90)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_wait)

    p = sub.add_parser("result", help="print a job's result without waiting")
    p.add_argument("job")
    p.add_argument("--fix-report", action="store_true", help="print the fix step's report")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_result)

    p = sub.add_parser("status", help="list active jobs (or --all) with owner and liveness")
    p.add_argument("job", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("cancel", help="cancel a job and end its process tree")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("job", nargs="?")
    g.add_argument("--all", action="store_true")
    p.set_defaults(fn=cmd_cancel)

    p = sub.add_parser("cleanup", help="sweep lost jobs and prune old records")
    p.add_argument("--prune-days", type=float, default=7)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_cleanup)

    p = sub.add_parser("_supervise")
    p.add_argument("job")
    p.set_defaults(fn=lambda a: supervise(a.job))

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except XhError as e:
        print(f"error: {e}", file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
