# session-handoff

Writes one compact Markdown handoff that lets a fresh agent session pick up the current work (goals, decisions, progress, files, blockers, and next steps) without re-asking you anything, and gives you a link to it.

## Use

Runs only when you invoke it by name, optionally with a focus for the next session, for example: "Use session-handoff, focus on the Safari export bug."

## Requirements

- Python 3.9+ to reserve the file (stdlib only). Without Python, the agent follows a manual fallback.

## Results

- One file, `handoff-<YYYYMMDD-HHMMSS>-<slug>.md`, in your temp directory: `%TEMP%\agent-skills\session-handoff\` on Windows, or `$TMPDIR/agent-skills-<uid>/session-handoff/` (or `/tmp/...`) elsewhere. The folder is private to you, files are never overwritten, and the OS may clean them up.
- The reply gives the native path and a `file://` link. In a remote or cloud session, it tells you how to copy the file out.
- Nothing is committed, uploaded, or saved to memory.
