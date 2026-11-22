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
3. **Reserve the file** (see [Output location](#output-location)).
4. **Write** the document into it using the [template](#document-template) and the [writing rules](#writing-rules).
5. **Report** the result to the user (see [Final response](#final-response)).

## Output Location

### Reserve the file

Run the bundled script, resolving its path from the directory that contains this `SKILL.md` (not from the working directory), with 2 to 5 words naming the goal (or the focus, when given):

```bash
python3 "<skill-dir>/scripts/new_handoff.py" fix safari export   # use "python" or "py" where "python3" is absent
```

It prints `{"path": "...", "uri": "file:///..."}` and guarantees:

- **Verified temp root.** Tries, in order, Windows `TEMP`, `TMP`, `TMPDIR`; Unix `TMPDIR`, `TEMP`, `TMP`, `/tmp`, `/var/tmp`. A root qualifies only if it is an absolute, existing directory where the handoff directory and file can be created (a read-only, full, or denied root falls through to the next), and it is private: on Windows, inside `%USERPROFILE%` (the profile is ACL'd to its owner); on Unix, either owned by the user and not writable by group or others, or sticky and owned by the user or `root` (like `/tmp`). Never falls back to the working directory; exits non-zero instead.
- **Private directory.** Windows: `<root>\agent-handoffs\`, inheriting the profile's owner-only ACL. Unix: `<root>/agent-handoffs-<uid>/`, mode `0700`, owned by the user. An existing entry that is a symlink, junction, non-directory, or owned by someone else stops the script.
- **No overwrites.** Creates `handoff-<YYYYMMDD-HHMMSS>-<slug>.md` exclusively, mode `0600`, with the slug capped at 60 characters; on a name clash only, it tries `-2`, `-3`, and so on, up to 99.

Write the document into the reserved file. Never write to any other path.

If the script exits non-zero, report its error to the user and stop. Do not pick another location.

### Without Python

Do the same steps by hand. If any check fails, stop and report it; do not pick another location.

1. Pick the root from the same candidate list, applying the same qualification (absolute, existing; Windows: inside `%USERPROFILE%`; Unix: check with `ls -ld` that it is yours and not group- or other-writable, or that it has the sticky bit `t` and is owned by you or `root`).
2. Create the handoff directory inside that root, and only there:
   - Windows (PowerShell): `$dir = New-Item -ItemType Directory -Force "$root\agent-handoffs"`; confirm `$dir.LinkType` is empty.
   - Unix: `dir="$root/agent-handoffs-$(id -u)"; umask 077; mkdir -p "$dir"`; confirm with `ls -ld` that it is a plain directory, owned by you, mode `drwx------`.
3. Create the file exclusively:
   - Windows: `New-Item -ItemType File -Path "$dir\handoff-<stamp>-<slug>.md"`. It fails on any existing entry. If the error says the name exists, try the next suffix, up to 99; on any other error, stop.
   - Unix: `mktemp "$dir/handoff-<stamp>-<slug>.XXXXXX"`. It creates a new `0600` file with a random suffix and fails on any existing entry. The name has no `.md` extension; that is acceptable.

### Link

Report both forms:

- The absolute path, in the platform's native form.
- The `file://` URI the script printed (by hand: `file:///C:/Users/<user>/AppData/Local/Temp/...` on Windows, `file:///tmp/...` on Unix, percent-encoding reserved characters).

### Remote sessions

A `file://` link opens on the user's machine. When the agent runs elsewhere (cloud container, remote shell, devcontainer, SSH), the link alone does not reach the file. In that case:

1. Deliver the file through a file-sharing or download mechanism the harness provides, if one exists and the user expects it.
2. Otherwise give a concrete copy-out command for that environment (for example `scp <host>:<path> .`, `docker cp <container>:<path> .`, or `cat <path>` to copy from the terminal), and offer to print the document inline.
3. Say that the file disappears with the environment.

Never upload or send the document anywhere the user has not asked for.

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
3. For a remote session, the retrieval step from [Remote sessions](#remote-sessions).

Do not paste the document into the reply.

## Validation

Before reporting, check the written file:

- [ ] Every template section with content is present; empty ones are omitted.
- [ ] "Start here" names the single next action.
- [ ] Every path is absolute and every URL is complete.
- [ ] Branch and change state were verified, or marked unverified.
- [ ] The focus, when given, appears in the header and drives Next steps.
- [ ] No secrets appear.
- [ ] The file exists at the reported path, inside the private handoff directory.
