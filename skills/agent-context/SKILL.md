---
name: agent-context
description: >-
  Standards for writing and reviewing agent context: skills (SKILL.md folders),
  instruction files, agent definitions, prompt files, AGENTS.md, and CLAUDE.md.
  Use whenever you create, revise, rename, or review any of these, or judge
  whether one is well built.
---

# Agent context

Write agent context that loads only when needed, says only what an agent would get wrong, and runs in any harness. This file holds the rules every feature type shares. Read the reference for the type you are working on.

## Feature types

Pick the narrowest type that fits.

| Need | Type | Portable form | Read |
| --- | --- | --- | --- |
| On-demand capability, optionally with scripts or references | Skill | `skills/<name>/SKILL.md` | [skills.md](references/skills.md) |
| Rules for every task in one repository | Repository instructions | `AGENTS.md` at the repository root | [repository-instructions.md](references/repository-instructions.md) |
| Rules for most work, or for a file pattern, across repositories | Instruction file | `<name>.instructions.md` | [instructions.md](references/instructions.md) |
| A role with its own context, scope, or tool limits | Agent | `<name>.agent.md` | [agents.md](references/agents.md) |
| A short, explicit, user-run task | Prompt | `<name>.prompt.md` | [prompts.md](references/prompts.md) |
| A guaranteed action at a lifecycle event | Hook | Harness configuration, not an instruction set | — |

- Prefer a skill to an instruction file unless the rule applies to most work. Always-on text costs context on every request; a skill costs only its description until it is used.
- Prefer a skill to a prompt. A user-only skill does the same job and can carry files.
- Use a hook, not text, when an action must happen every time. Instructions are advisory; hooks are enforced.

## Workflow

1. **Intent first.** For a new feature, write its intent file from the user's ask before anything else, keeping their words for goals and requirements. If one already exists, build from it and leave it unedited. For an existing feature, read the intent file first, then append a log entry after changing the feature. If it has none, a review only reports that it is missing; a revision adds one, built from the user's stated asks and the feature's history, with anything inferred marked `[agent]`. See [readme-and-intent.md](references/readme-and-intent.md).
2. **Choose the type** from the table above and read its reference.
3. **Name** it ([Naming](#naming)).
4. **Write the body**, then the description last, once the body is settled.
5. **Validate** with the [Checklist](#checklist) and the type's own checks.

## Naming

- Lowercase letters, digits, and single hyphens. Two or three words. A skill's name must also equal its folder name.
- Use a noun phrase for a feature that covers a subject: `go-development`, `release-process`, `api-design`.
- Use verb-object only for a feature that performs one explicit action: `deploy-preview`, `rotate-keys`.
- Do not use gerunds: `managing-secrets` becomes `secret-management`.
- Drop filler such as `helper`, `utils`, `tool`, or `my`.

## Descriptions

The description is often the only text an agent sees before it decides to load or delegate. It must make that decision immediate.

- Write one to three sentences, aiming for 300 characters or fewer.
- First, say what the feature does or covers, in the nouns users actually type.
- Then add "Use when …" with concrete triggers. Add "Not for …" only when a neighbouring feature could be confused with this one.
- Do not list every feature, market it, or repeat the name.
- Test it: from the name and description alone, an agent must answer yes or no correctly for five realistic requests, including two near-misses.

## Writing style

- Write for a capable agent. Include only what it would get wrong without being told. Cut background, motivation, and generic advice.
- Give a rule, and add the reason in a clause when the reason is not obvious. Use plain imperatives. Do not use all-caps MUST, banned-word lists, or personas.
- There is no mandatory section template. Use the sections the task needs.
- Prefer lists, tables, and one sharp example over prose or several examples.
- Do not restate what a formatter, linter, or script enforces. Name the tool instead.
- Keep it harness-neutral. Say "run", "read", or "edit", not harness tool names, slash commands, invocation syntax, or harness paths. If a feature truly needs one harness, say so where users will see it.
- Put the most important rule first. Agents weigh early text more, and long files get skimmed.

## Scope and composition

Each feature must stand alone. A user may install it without any of its neighbours.

- Never name another skill, instruction file, or agent as a dependency or a source of rules. Refer to it by capability instead, for example "follow any standards the user has for Python development".
- Cover only the feature's own subject. Do not set rules for adjacent domains, such as code style, testing, or commit conventions, that other features or user instructions may own. State only what this subject needs on top of them.
- Copy a small piece of shared logic in, rather than linking to a file in another feature's folder.
- Never contradict another always-on file. If two rules collide, fix the source, not the reader.

## Checklist

- [ ] The type is the narrowest that fits.
- [ ] Every line is something a capable agent would otherwise get wrong. Nothing restates a tool, a linter, or another feature's subject.
- [ ] No other feature is named as a dependency or source of rules.
- [ ] Description test: five requests, including near-misses, are judged correctly from the description alone.
- [ ] Harness-neutral, or the limit is stated where users see it.
- [ ] `npx markdownlint-cli2` passes, if the repository uses it.
- [ ] The intent file still matches. A new log entry records what changed and why.
- [ ] The type reference's own checks pass.

## References

- [skills.md](references/skills.md): read when building or reviewing a skill. Covers layout, metadata, progressive disclosure, paths, scripts, and the checker.
- [metadata.md](references/metadata.md): read when setting a skill's invocation flags, `compatibility`, or harness sidecar files.
- [paths.md](references/paths.md): read when a skill writes files outside the user's working files.
- [scripts.md](references/scripts.md): read when adding or changing a skill script.
- [cli.md](references/cli.md): read when deciding whether a skill needs a CLI, or when a CLI needs config, credentials, subcommands, or more than about 300 lines.
- [instructions.md](references/instructions.md): read when writing an instruction file.
- [agents.md](references/agents.md): read when writing an agent definition.
- [prompts.md](references/prompts.md): read when writing a prompt file.
- [repository-instructions.md](references/repository-instructions.md): read when writing `AGENTS.md`, `CLAUDE.md`, or other repository-wide instructions.
- [readme-and-intent.md](references/readme-and-intent.md): read when writing or updating a README or intent file.
