---
name: Codex Commit Attribution
description: Attribute Codex-assisted Git commits while preserving human authorship.
applyTo: "**"
---

# Codex commit attribution

When Codex creates or amends a commit, or writes a squash-merge message:

- Keep the configured human Git author and all existing trailers.
- End the message with exactly one trailer, after a blank line:

  ```text
  Co-authored-by: Codex <noreply@openai.com>
  ```

- If the repository or user config sets a different Codex identity, use that one.
- Never rewrite published history only to add this trailer. Fix unpublished commits only when asked.
