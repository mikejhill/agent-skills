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
- 2026-11-22: [agent] Codex review (gpt-6.2-astra) fixes: `scripts/new_handoff.py` reserves the file (verified temp dir, never the cwd; per-user `0700` directory on Unix; exclusive `0600` create with suffix retry); `agents/openai.yaml` sets `allow_implicit_invocation: false` because Codex ignores `disable-model-invocation`; remote sessions get a copy-out step instead of a bare `file://` link.
- 2026-11-22: [agent] Codex round 2 fixes: Windows temp roots must sit inside `%USERPROFILE%`, the handoff directory gets a user-only ACL via `icacls` (fail closed), junctions are rejected; script path resolves from the skill directory; manual fallback requires absolute roots, reuses the chosen root, and retries only on name clashes (max 99).
- 2026-11-22: [agent] Codex round 3 fixes, simplifying instead of adding layers: dropped `icacls` (trust the profile's owner-only ACL, roots must sit inside `%USERPROFILE%`); Unix roots must be user-owned and private or sticky; unwritable roots fall through to the next candidate while privacy failures stop; slug capped at 60 chars; Unix fallback uses `mktemp`. Threat model: a personal machine or single-user container; the goal is no accidental exposure or overwrite, not defense against a hostile local admin.
- 2026-11-22: [agent] Codex round 4 fixes: Unix fallback binds `dir` before use; read-only, full, or denied roots (including at file creation) fall through to the next root; sticky roots must be owned by the user or root. Declined: verifying Windows ACLs under `%USERPROFILE%` (needs a deliberately misconfigured profile; outside the threat model above).
- 2026-11-22: Keep `agents/openai.yaml` in the skill: an inert sidecar elsewhere and the only way to enforce explicit-only invocation on Codex. Harness sidecar files are acceptable; harness-specific content is not.
