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
    assert_ok(run(PY, SKILLS / "skill-development" / "scripts" / "check_skill.py", SKILLS))


@pytest.mark.parametrize("script", [
    "browser-control/scripts/browser.py",
    "cross-harness/scripts/xh.py",
    "efficient-tool-calls/scripts/shell_probe.py",
    "session-handoff/scripts/new_handoff.py",
    "skill-development/scripts/check_skill.py",
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


# Script languages that a CI job lints or tests. Adding a script in another language
# fails test_every_script_language_has_ci until a job covers it and its suffix is listed.
COVERED_SUFFIXES = {
    ".py": "ruff + pytest",
    ".sh": "shellcheck", ".bash": "shellcheck",
    ".ps1": "PSScriptAnalyzer", ".psm1": "PSScriptAnalyzer", ".psd1": "PSScriptAnalyzer",
}
# Single files covered by a dedicated check instead of a language-wide job.
COVERED_FILES = {
    "skills/mermaid-diagrams/scripts/mermaid-export.mjs": "test_mermaid_export_parses",
}
CODE_SUFFIXES = {
    ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".tsx", ".jsx", ".go", ".rs", ".rb", ".java",
    ".kt", ".kts", ".cs", ".fs", ".lua", ".pl", ".pm", ".php", ".swift", ".c", ".cc", ".cpp",
    ".h", ".hpp", ".zsh", ".fish", ".bat", ".cmd", ".r", ".jl", ".dart", ".scala", ".groovy",
}
SHEBANG_SUFFIX = {"python": ".py", "python3": ".py", "bash": ".sh", "sh": ".sh", "dash": ".sh",
                  "pwsh": ".ps1", "node": ".js", "deno": ".ts", "bun": ".ts", "ruby": ".rb",
                  "perl": ".pl", "zsh": ".zsh", "lua": ".lua"}
# Bundled data, not code the library maintains: vendored libraries, templates, examples.
NOT_SCRIPTS = ("/assets/", "/examples/")


def script_suffix(path: Path) -> str | None:
    """The language suffix of a tracked file, from its name or else its shebang."""
    suffix = path.suffix.lower()
    if suffix in COVERED_SUFFIXES or suffix in CODE_SUFFIXES:
        return suffix
    if suffix:
        return None
    try:
        first = path.read_bytes()[:200].split(b"\n", 1)[0].decode("utf-8", "replace")
    except OSError:
        return None
    if not first.startswith("#!"):
        return None
    words = first[2:].split()
    if words and words[0].endswith("/env"):
        words = [w for w in words[1:] if not w.startswith("-")]
    name = Path(words[0]).name if words else ""
    return SHEBANG_SUFFIX.get(name, f"#!{name}")


def test_every_script_language_has_ci() -> None:
    uncovered = []
    for path in tracked("*"):
        rel = path.relative_to(REPO).as_posix()
        if any(part in f"/{rel}" for part in NOT_SCRIPTS) or rel in COVERED_FILES:
            continue
        suffix = script_suffix(path)
        if suffix and suffix not in COVERED_SUFFIXES:
            uncovered.append(f"{rel} ({suffix})")
    assert not uncovered, (
        "These scripts use a language no CI job lints or tests:\n  " + "\n  ".join(uncovered)
        + "\nAdd a job for the language to .github/workflows/ci.yml, list it under ci-pass, and add"
        " its suffix to COVERED_SUFFIXES (or one file to COVERED_FILES) in .github/ci/test_scripts.py.")


def test_script_language_guard_flags_new_languages(tmp_path: Path) -> None:
    (tmp_path / "tool.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "run").write_text("#!/usr/bin/env -S deno run\n", encoding="utf-8")
    (tmp_path / "ok").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# notes\n", encoding="utf-8")
    assert script_suffix(tmp_path / "tool.go") == ".go"
    assert script_suffix(tmp_path / "run") == ".ts"
    assert script_suffix(tmp_path / "ok") == ".py"
    assert script_suffix(tmp_path / "notes.md") is None
