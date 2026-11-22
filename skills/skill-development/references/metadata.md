# Metadata

## Spec fields

From the [Agent Skills specification](https://agentskills.io/specification):

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | Yes | 1-64 characters: `a-z`, `0-9`, and `-`. No leading, trailing, or doubled hyphen. Must equal the folder name. |
| `description` | Yes | 1-1024 characters. Says what the skill does and when to use it. |
| `license` | No | A short license name, or a path to a bundled license file. |
| `compatibility` | No | 1-500 characters describing environment requirements. |
| `metadata` | No | A map of string keys to string values. |
| `allowed-tools` | No | Experimental. A space-separated list of pre-approved tools. |

- Use `>-` folded scalars for a description longer than one line. Quote any value that contains a colon followed by a space, or starts with a YAML indicator character.
- Use `compatibility` for facts that block a run, such as `Requires Python 3.9+ and network access to api.github.com` or `Claude Code only: drives its subagent API`. Do not use it for preferences.
- Put a `version` or `owner` in `metadata`, not in new top-level keys.

## Invocation flags

These are harness extensions, not spec fields. Harnesses that do not know a flag ignore it, so the skill stays portable.

| Need | Frontmatter | Codex sidecar |
| --- | --- | --- |
| Default: both the user and the model may invoke | none | none |
| Only the user may invoke | `disable-model-invocation: true` | `agents/openai.yaml` with `policy.allow_implicit_invocation: false` |
| Only the model may invoke, because it is background knowledge rather than a command | `user-invocable: false` | none |
| Takes an argument when the user invokes it | `argument-hint: "[what to pass]"` | none |

Restrict model invocation only when a run has effects the user must choose:

- It sends, publishes, deploys, deletes, or spends money.
- It starts long or costly work, such as spawning agents or full test suites.
- It writes outside the workspace.
- Its description would otherwise trigger on ordinary requests where it is wrong.

A skill that only informs how work is done stays model-invocable. Never set both restrictions, because that makes the skill unreachable.

The Codex sidecar is required for user-only skills, because Codex ignores `disable-model-invocation`:

```yaml
# agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

Sidecar files like this are acceptable. Harness-specific content in `SKILL.md` is not.
