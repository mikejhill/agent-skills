# Intent

Let the user end a session and start a fresh one without losing its goals, context, progress, or next steps, by writing one handoff document on request.

## Goals

1. A new session can resume from the document alone, without re-asking anything the previous session settled.
2. Runs only when the user invokes it; the model never triggers it on its own.
3. Covers the session goals, key paths and URLs, critical context, steps taken, artifacts, blockers, and next steps.
4. Accepts an optional next-session focus that shapes the document.
5. Writes to the user's temp directory on Windows, macOS, and Linux, and returns a link to the file.
6. Efficient: compact enough to read in one pass, with no padding.

## Log

- 2026-11-22: Created. User-invocable only, optional focus argument, output in the platform temp directory with a link.
- 2026-11-22: [agent] Files go under `<temp>/agent-handoffs/` with timestamped, never-overwritten names; the reply gives both the native path and a `file://` URI, and warns when the environment is ephemeral.
