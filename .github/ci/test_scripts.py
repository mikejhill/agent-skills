"""Smoke tests for the scripts that skills ship.

Run from the repository root:

    python -m pytest

Each skill's own unittest files under skills/*/tests are collected alongside
these. The skills' end-to-end smoke scripts (tests/smoke_test.py) are plain
scripts, so they run here as subprocesses.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"
PY = sys.executable
IN_CI = os.environ.get("CI") == "true"


def run(*args: str | Path, timeout: int = 120, env: dict[str, str] | None = None,
        cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, env=env, cwd=cwd, check=False)


def run_tree(*args: str | Path, timeout: int, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a long smoke script in its own process group; on timeout, kill the whole tree.

    Output goes to files, not pipes, so a leftover grandchild holding an inherited handle
    cannot block the wait after the kill. Brokers and supervisors that the scripts start in
    their own sessions are outside the group; the scripts stop them in their own cleanup, and
    CI runners are discarded after the job.
    """
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as out, \
            tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as err:
        group = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
                 else {"start_new_session": True})
        proc = subprocess.Popen([str(a) for a in args], stdout=out, stderr=err, cwd=cwd, **group)
        try:
            code = proc.wait(timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False)
            else:
                os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(30)
            out.seek(0)
            pytest.fail(f"timed out after {timeout} s; process group killed\n{out.read()}")
        out.seek(0)
        err.seek(0)
        return subprocess.CompletedProcess(args, code, out.read(), err.read())


def assert_ok(proc: subprocess.CompletedProcess[str]) -> None:
    assert proc.returncode == 0, f"exit {proc.returncode}\n--- stdout\n{proc.stdout}\n--- stderr\n{proc.stderr}"


def tracked(pattern: str) -> list[Path]:
    out = run("git", "ls-files", "-z", pattern, cwd=REPO).stdout
    return [REPO / p for p in out.split("\0") if p]


def test_skills_meet_skill_development_standard() -> None:
    assert_ok(run(PY, SKILLS / "agent-context" / "scripts" / "check_skill.py", SKILLS))


@pytest.mark.parametrize("script", [
    "browser-control/scripts/browser.py",
    "cross-harness/scripts/xh.py",
    "efficient-tool-calls/scripts/shell_probe.py",
    "session-handoff/scripts/new_handoff.py",
    "agent-context/scripts/check_skill.py",
])
def test_cli_help(script: str) -> None:
    proc = run(PY, SKILLS / script, "--help")
    assert_ok(proc)
    assert "usage" in proc.stdout.lower()


def test_cross_harness_smoke() -> None:
    skill = SKILLS / "cross-harness"
    assert_ok(run_tree(PY, skill / "tests" / "smoke_test.py", timeout=600, cwd=skill))


def test_browser_control_smoke() -> None:
    skill = SKILLS / "browser-control"
    proc = run_tree(PY, skill / "tests" / "smoke_test.py", timeout=900, cwd=skill)
    if not IN_CI and proc.returncode != 0 and "no chromium found" in (proc.stdout + proc.stderr).lower():
        pytest.skip("no Chromium-family browser on this machine")
    assert_ok(proc)


def test_html_report_example_is_current(tmp_path: Path) -> None:
    skill = SKILLS / "html-report"
    out = tmp_path / "sample-report.html"
    assert_ok(run(PY, skill / "scripts" / "build_report.py", skill / "examples" / "sample-report.src.html", out))
    def text(path: Path) -> str:  # checkouts may convert line endings
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    assert text(out) == text(skill / "examples" / "sample-report.html"), (
        "examples/sample-report.html is stale: rebuild it with scripts/build_report.py")
    assert_ok(run(PY, skill / "scripts" / "check_report.py", out))


def test_html_report_check_flags_unbuilt_template() -> None:
    skill = SKILLS / "html-report"
    proc = run(PY, skill / "scripts" / "check_report.py", skill / "assets" / "template.html")
    assert proc.returncode == 1
    assert "vendor placeholder not inlined" in proc.stdout


def test_new_handoff_reserves_private_file(tmp_path: Path) -> None:
    # Windows accepts only temp roots inside %USERPROFILE%, so use a synthetic profile.
    temp = tmp_path / "AppData" / "Local" / "Temp"
    temp.mkdir(parents=True, mode=0o700)
    env = dict(os.environ, USERPROFILE=str(tmp_path), TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp))
    proc = run(PY, SKILLS / "session-handoff" / "scripts" / "new_handoff.py", "ci", "smoke", "test", env=env)
    assert_ok(proc)
    path = Path(json.loads(proc.stdout)["path"])
    assert path.is_file() and path.stat().st_size == 0
    assert path.name.startswith("handoff-") and path.name.endswith("-ci-smoke-test.md")
    assert temp.resolve() in path.resolve().parents
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_mermaid_export_parses() -> None:
    assert_ok(run("node", "--check", SKILLS / "mermaid-diagrams" / "scripts" / "mermaid-export.mjs"))


def test_tracked_json_parses() -> None:
    files = tracked("*.json")
    assert files, "expected at least one tracked JSON file"
    for f in files:
        json.loads(f.read_text(encoding="utf-8"))


# Script languages that a CI job lints or tests, matching the selectors in .github/ci/lint.sh
# and psscriptanalyzer.ps1. Those selectors are case-sensitive Git pathspecs and Ruff globs, so
# these suffixes match case-sensitively too: helper.PS1 is not analyzed and is not covered.
# Adding a script in another language fails test_every_script_language_has_ci until a job
# covers it and it is listed here.
COVERED_SUFFIXES = {
    ".py": "ruff + pytest", ".pyi": "ruff", ".ipynb": "ruff",
    ".sh": "shellcheck", ".bash": "shellcheck",
    ".ps1": "PSScriptAnalyzer", ".psm1": "PSScriptAnalyzer", ".psd1": "PSScriptAnalyzer",
}
# lint.sh also sends any file with a sh/bash/dash/ksh shebang to shellcheck.
COVERED_SHEBANG = re.compile(r"^#!.*\b(ba|da|k)?sh\b")
# Single files covered by a dedicated check instead of a language-wide job.
COVERED_FILES = {
    "skills/mermaid-diagrams/scripts/mermaid-export.mjs": "test_mermaid_export_parses",
}
# Outside skills/, source-code suffixes are flagged wherever they appear (compared
# lowercased), since a script run as `deno run x.ts` needs no shebang. Inside a skill every
# file must be covered or known data, so an unlisted language cannot slip through.
SOURCE_SUFFIXES = {
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx", ".go", ".rs", ".rb", ".pl",
    ".pm", ".php", ".lua", ".java", ".kt", ".kts", ".scala", ".groovy", ".cs", ".csx", ".fs",
    ".fsx", ".vb", ".vbs", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".r", ".jl",
    ".ex", ".exs", ".erl", ".dart", ".zig", ".nim", ".clj", ".hs", ".ml", ".tcl", ".awk",
    ".zsh", ".fish", ".nu", ".bat", ".cmd", ".py", ".pyi", ".ipynb", ".sh", ".bash", ".ps1",
    ".psm1", ".psd1",
}
# Data and documentation (compared lowercased).
NON_CODE_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonc", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".csv", ".tsv",
    ".html", ".htm", ".css", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".xml",
    ".mmd", ".lock",
}
# Data files matched by whole name, since Path(".gitignore").suffix is empty.
NON_CODE_NAMES = {".gitignore", ".gitattributes", ".gitkeep", ".editorconfig", "LICENSE", "NOTICE"}
# Bundled data folders directly under skills/<name>/, not code the library maintains:
# vendored libraries, templates, examples.
DATA_FOLDERS = {"assets", "examples"}


def skill_rel(rel: str) -> str:
    """Map a harness-specific skill path (harnesses/<h>/skills/...) to the root layout."""
    parts = rel.split("/")
    if len(parts) > 3 and parts[0] == "harnesses" and parts[2] == "skills":
        return "/".join(parts[2:])
    return rel


def in_data_folder(rel: str) -> bool:
    parts = skill_rel(rel).split("/")
    return len(parts) > 3 and parts[0] == "skills" and parts[2] in DATA_FOLDERS


def shebang(path: Path) -> str:
    try:
        with path.open("rb") as f:
            head = f.readline(4096)  # lint.sh reads the whole first line
    except OSError:
        return ""
    line = head.rstrip(b"\r\n").decode("utf-8", "replace")
    return line if line.startswith("#!") else ""


def notebook_language(path: Path) -> str:
    """The notebook's language as Ruff reads it; Ruff skips notebooks that are not Python."""
    try:
        meta = json.loads(path.read_text(encoding="utf-8")).get("metadata", {})
    except (OSError, ValueError, AttributeError):
        return "unreadable"
    lang = (meta.get("language_info") or {}).get("name") or (meta.get("kernelspec") or {}).get("language")
    return str(lang or "python").lower()


def uncovered_reason(path: Path, rel: str) -> str | None:
    """Why a tracked file is code that no CI job checks, or None if it is covered or not code."""
    if rel in COVERED_FILES:
        return None
    if path.suffix == ".ipynb":
        lang = notebook_language(path)
        return None if lang == "python" else f"{lang} notebook; Ruff checks Python notebooks only"
    if path.suffix in COVERED_SUFFIXES:
        return None
    line = shebang(path)
    if line:
        if COVERED_SHEBANG.match(line):
            return None
        return f"shebang {line!r}; no lint job selects it (use a covered extension or add a job)"
    suffix = path.suffix.lower()
    if path.name in NON_CODE_NAMES or suffix in NON_CODE_SUFFIXES:
        return None
    if skill_rel(rel).startswith("skills/"):
        return f"{path.suffix or 'no extension'}: not a covered language or a known data type"
    if suffix in SOURCE_SUFFIXES:
        return f"{path.suffix} source file; no lint job selects this suffix"
    return None


def test_every_script_language_has_ci() -> None:
    uncovered = []
    for path in tracked("*"):
        rel = path.relative_to(REPO).as_posix()
        if in_data_folder(rel):
            continue
        reason = uncovered_reason(path, rel)
        if reason:
            uncovered.append(f"{rel}: {reason}")
    assert not uncovered, (
        "These files are code that no CI job lints or tests:\n  " + "\n  ".join(uncovered)
        + "\nAdd a job for the language to .github/workflows/ci.yml, list it under ci-pass, and add"
        " its suffix to COVERED_SUFFIXES (or one file to COVERED_FILES) in .github/ci/test_scripts.py."
        " Data files belong in NON_CODE_SUFFIXES.")


def test_script_language_guard_classification(tmp_path: Path) -> None:
    scripts = tmp_path / "skills" / "x" / "scripts"
    scripts.mkdir(parents=True)
    cases = {
        "tool.go": ("package main\n", True),
        "tool.exs": ("IO.puts 1\n", True),
        "run": ("#!/usr/bin/env -S deno run\n", True),
        "pyrun": ("#!/usr/bin/env python3\n", True),   # ruff selects *.py only
        "psrun": ("#!/usr/bin/env pwsh\n", True),       # PSScriptAnalyzer selects *.ps1 only
        "helper.PS1": ("Write-Output 1\n", True),       # pathspec *.ps1 is case-sensitive
        "kshrun": ("#!/bin/ksh\n", False),             # lint.sh sends it to shellcheck
        "tool.py": ("print(1)\n", False),
        "stubs.pyi": ("x: int\n", False),
        "nb.ipynb": ("{}\n", False),
        "jl.ipynb": ('{"metadata": {"language_info": {"name": "julia"}}}\n', True),
        "jlk.ipynb": ('{"metadata": {"kernelspec": {"language": "Julia"}}}\n', True),
        "longbang": ("#!/" + "x" * 300 + "/bash\n", False),
        ".gitignore": ("*.tmp\n", False),
        "notes.md": ("# notes\n", False),
    }
    for name, (text, flagged) in cases.items():
        path = scripts / name
        path.write_text(text, encoding="utf-8")
        rel = path.relative_to(tmp_path).as_posix()
        assert (uncovered_reason(path, rel) is not None) == flagged, name
    # Inside a skill, any unknown file type is flagged in any folder: `dotnet fsi` needs no shebang.
    bin_dir = tmp_path / "skills" / "x" / "bin"
    bin_dir.mkdir()
    render = bin_dir / "render.fsx"
    render.write_text("printfn \"1\"\n", encoding="utf-8")
    assert uncovered_reason(render, render.relative_to(tmp_path).as_posix()) is not None
    # Data folders are exempt only directly under a skill, not when the skill is named after one.
    assert in_data_folder("skills/x/assets/vendor.js")
    assert in_data_folder("skills/x/examples/demo.ts")
    assert not in_data_folder("skills/assets/scripts/render.ts")
    assert not in_data_folder("skills/x/scripts/assets/render.ts")
    # Harness-specific skills follow the same rules.
    assert in_data_folder("harnesses/claude/skills/x/assets/vendor.js")
    assert not in_data_folder("harnesses/claude/skills/x/scripts/render.ts")
    assert not in_data_folder("harnesses/claude/assets/x/vendor.js")
    hs = tmp_path / "harnesses" / "claude" / "skills" / "x" / "bin"
    hs.mkdir(parents=True)
    hrender = hs / "render.fsx"
    hrender.write_text("printfn \"1\"\n", encoding="utf-8")
    assert uncovered_reason(hrender, hrender.relative_to(tmp_path).as_posix()) is not None


@pytest.mark.skipif(os.name == "nt" or shutil.which("bash") is None, reason="needs bash")
def test_lint_sh_passes_non_ascii_shell_names(tmp_path: Path) -> None:
    lint = (REPO / ".github" / "ci" / "lint.sh").read_text(encoding="utf-8")
    func = lint[lint.index("shell_files() {"):]
    func = func[:func.index("\n}\n") + 3]
    (tmp_path / "résumé").write_text("#!/bin/sh\necho 1\n", encoding="utf-8")
    assert_ok(run("git", "init", "-q", cwd=tmp_path))
    assert_ok(run("git", "add", "résumé", cwd=tmp_path))
    proc = run("bash", "-c", func + "shell_files", cwd=tmp_path)
    assert_ok(proc)
    assert proc.stdout.splitlines() == ["résumé"]
