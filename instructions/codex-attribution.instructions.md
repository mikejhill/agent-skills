---
name: Codex Commit Attribution
description: Preserve human authorship and attribute Codex-assisted Git commits.
applyTo: "**"
---

# Codex commit attribution

For every Codex-assisted Git commit that Codex creates or amends, including a
squash-merge message it controls, preserve the configured human Git author and
all existing legitimate trailers. Include exactly one final attribution trailer,
separated from the message body by a blank line:

```text
Co-authored-by: Codex <noreply@openai.com>
```

This identity matches the user's configured Codex `commit_attribution`. Verify
the effective local/repository convention rather than inventing an email.
Check the resulting message before publication. Do not attribute contributions
from another harness to Codex when Codex did not assist.

Do not rewrite published history solely to add attribution. Correct existing
unpublished commits only when authorized, preserving unrelated work and human
authorship. Maintain this instruction in the SkillSinc canonical library and
use its reviewed plan/sync workflow; never edit distributed copies as the fix.
