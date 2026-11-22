---
name: session-handoff
description: >-
  Write a handoff document that lets a fresh agent session resume the current
  session's work, save it in the user's temp directory, and return a link to it.
  Run only when the user explicitly invokes it.
argument-hint: "[optional focus for the next session]"
disable-model-invocation: true
---

# Session Handoff

## Objective

Capture the current session in one compact Markdown document that a new session, with no access to this conversation, can read once and continue the work without re-asking the user anything already settled. Save it to the user's temp directory and give the user a link.

## Scope

**In-scope:**

- Summarizing the current session's goals, context, progress, artifacts, blockers, and next steps
- Narrowing the document to a next-session focus the user supplies
- Writing the file to the platform temp directory and reporting its location

**Out-of-scope:**

- Auto-triggering. Run this skill only when the user invokes it by name. Never start it because a session is long, a context limit is near, or work is ending.
- Committing, pushing, uploading, or sharing the document anywhere
- Persisting facts to long-term memory or instruction files
- Starting the next session

## Input

| Input | Required | Use |
| ----- | -------- | --- |
| Next-session focus | No | Free text after the invocation. When present, lead with it, order next steps around it, and drop context that does not serve it. When absent, hand off the whole session. |

Treat the focus as the user's priority for the next session, not as a replacement for the session's goals. If the focus contradicts a goal or decision made earlier, record both and flag the conflict under Open questions.

## Procedure

1. **Gather.** Review the whole conversation, not only recent turns. Collect goals, decisions and their reasons, constraints the user stated, files read or changed, commands run, results, errors, and anything still pending.
2. **Verify cheaply.** Where tools allow, confirm facts the next session depends on instead of recalling them: current branch and uncommitted changes (`git status`, `git log -1`), whether referenced files exist, and PR or CI state if one was in play. Do not run long builds or tests for this. Mark anything unverified as such.
3. **Resolve the temp directory** (see [Output location](#output-location)).
4. **Write** the document using the [template](#document-template) and the [writing rules](#writing-rules).
5. **Report** the result to the user (see [Final response](#final-response)).

## Output Location

### Temp directory

Use the first that resolves to an existing, writable directory:

1. `TMPDIR` (macOS, most Unix)
2. `TEMP`, then `TMP` (Windows)
3. `/tmp` (Unix fallback)

Equivalent one-liners return the same answer:

```bash
# POSIX shell
dir="${TMPDIR:-${TEMP:-${TMP:-/tmp}}}"
```

```powershell
# PowerShell (any OS)
$dir = [System.IO.Path]::GetTempPath()
```

```python
import tempfile; d = tempfile.gettempdir()
```

### File path

```text
<temp>/agent-handoffs/handoff-<YYYYMMDD-HHMMSS>-<slug>.md
```

- Create `agent-handoffs/` if missing.
- `<YYYYMMDD-HHMMSS>` is local time when written.
- `<slug>` is 2 to 5 lowercase hyphenated words naming the goal (or the focus, when given), for example `fix-safari-export`.
- Never overwrite an existing file. If the name exists, append `-2`, `-3`, and so on.
- Use the platform's native separators in the path you report.

### Link

Report both forms:

- The absolute path, in the platform's native form (`C:\Users\<user>\AppData\Local\Temp\agent-handoffs\...` on Windows, `/tmp/agent-handoffs/...` on Unix).
- A `file://` URI: `file:///C:/Users/<user>/AppData/Local/Temp/agent-handoffs/...` on Windows (forward slashes, drive letter after three slashes), `file:///tmp/agent-handoffs/...` on Unix. Percent-encode spaces and other reserved characters.

If the session runs in an ephemeral or remote environment (a cloud container, a remote shell), say that the file lives there and will not survive the environment, so the user can copy it out.

## Document Template

Omit a section only when it would be empty; never pad. Keep the headings so a reader can scan.

````markdown
# Handoff: <goal in one line>

- Created: <ISO 8601 local timestamp with offset>
- Working directory: <absolute path, or "n/a">
- Repository and branch: <remote URL or path> @ <branch> (<short SHA>, <clean | N uncommitted files>)
- Next-session focus: <user-supplied focus, or "Continue the session goals">

## Start here

<3 to 5 sentences: what the work is, where it stands now, and the single next action. A reader who stops here can still begin.>

## Goals

1. <Primary goal, with the definition of done>
2. <Secondary goals>

## Critical context

- <Decisions made, each with its reason>
- <User preferences and constraints that must keep holding>
- <Non-obvious facts learned the hard way: quirks, gotchas, environment details>
- <Approaches tried and rejected, and why, so they are not retried>

## Key locations

| What | Path or URL | Notes |
| ---- | ----------- | ----- |
| <repo, file, doc, dashboard, PR, issue> | <absolute path or full URL> | <why it matters> |

## Progress so far

1. <Step taken, with its outcome>
2. <...>

## Artifacts

| Artifact | Location | State |
| -------- | -------- | ----- |
| <file changed or created, branch, PR, report, log> | <path or URL> | <draft, committed, pushed, merged, failing, ...> |

## Blockers and risks

- <Blocker: what is stuck, why, and what would unblock it>
- <Risk or known failure: symptom and current hypothesis>

## Open questions

- <Question the next session or the user must answer, and who can answer it>

## Next steps

1. <Concrete action, with the command, file, or URL it starts from>
2. <...>
````

## Writing Rules

- Write for a reader with zero context. Expand acronyms and internal names on first use. Never write "as discussed", "the earlier approach", or "the file above".
- Be specific. Use absolute paths, full URLs, exact branch names, exact error messages, exact commands. A vague pointer costs the next session a search.
- Keep it short. Target under 150 lines. Prefer bullets and tables over prose. Summarize logs and long outputs; quote only the decisive lines.
- Separate fact from guess. Mark anything unverified or inferred with "(unverified)" or "(hypothesis)".
- Record why, not only what, for every decision and rejected approach.
- Make next steps executable: each starts with a verb and names its starting point. Order them by the focus when one was given, otherwise by dependency.
- Never include secrets: tokens, passwords, API keys, cookies, private keys, or connection strings with credentials. Name where the secret lives instead (for example "the API key in the `FOO_TOKEN` environment variable").

## Final Response

Reply to the user with only:

1. The link, as a Markdown link whose target is the `file://` URI and whose text is the absolute path.
2. One line stating the goal and next step the handoff leads with.
3. The ephemeral-environment warning, if it applies.

Do not paste the document into the reply.

## Validation

Before reporting, check the written file:

- [ ] Every template section with content is present; empty ones are omitted.
- [ ] "Start here" names the single next action.
- [ ] Every path is absolute and every URL is complete.
- [ ] Branch and change state were verified, or marked unverified.
- [ ] The focus, when given, appears in the header and drives Next steps.
- [ ] No secrets appear.
- [ ] The file exists at the reported path.
