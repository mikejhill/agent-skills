# Intent

Teach agents to build and review skills that are concise, trigger accurately, load detail lazily, and follow one consistent set of library conventions across every harness. Replaces `writing-ai-instructions`.

## Goals

1. Skills an agent builds with this skill follow every requirement below, and this skill follows them itself.
2. Skill content is concise and to the point. Nothing an agent would do correctly unprompted is included.
3. Descriptions let an agent decide immediately and accurately whether to load the skill.
4. Detail that is not always needed loads lazily through progressive disclosure.
5. Skills are consistent with each other in naming, metadata, structure, paths, file naming, and CLI usage.
6. Skills work in every harness unless there is a specific reason not to.

## Requirements

- Skill contents are concise and to the point.
- Descriptions are concise and give agents clear information, so they can immediately and accurately decide whether to pull in the skill.
- Use progressive discovery for more detailed elements: lazy loading of details that are not always necessary, such as scenario-specific factors, detailed factors for higher-depth runs, troubleshooting, and scripts.
- Use a standard path and file structure for contents.
- Every skill has a `README.md` and an `INTENT.md`. Agents are unlikely to read either except when developing the skill.
  - `README.md` is human-facing for users. It explains what the skill does, how it should be seen, and how it should be used, plus anything users should be aware of: dependencies, environment constraints, expected results, security factors, and the like. Humans typically give it no more than a cursory glance, so keep it short.
  - `INTENT.md` is human-facing and agent-facing for skill developers. It explains the skill's purpose, constraints, requirements, and desired outcome. It is used during construction and iteration, and it should generally be possible to reconstruct the skill from it alone. It is often agent-written but must clearly reflect the asks of the human operator who created the skill.
- Consistent naming: concise and clear. Use nouns when a skill covers a subject (`project-setup`, `java-development`, `python-development`). Avoid gerunds. Limit verbs to skills that perform an explicit action.
- Consistent metadata that follows the Agent Skills specification as closely as possible. Be conservative but intelligent with user-invocation and model-invocation flags.
- Consistent path patterns for shared references, such as how temp directories are referenced and used.
- Ephemeral, temporary, or transitory files use a standard naming convention that includes the current date and/or time.
- Skills that use CLIs follow a common pattern for placing and executing them. CLIs prefer a limited set of generally portable or widely available languages. When languages or behavior are OS-dependent, state this and/or provide solutions for other OSes.
- Skills are compatible across all harnesses unless there is a specific reason not to be. A skill limited to specific harnesses says so clearly in its README.

## Log

- 2026-11-22: Rebuilt from scratch to replace `writing-ai-instructions`, which was out of date and imposed unwanted characteristics on created skills. Renamed. Requirements above are from the operator's request.
- 2026-11-22: [agent] Named `skill-development`: a noun phrase that matches `skill-cli-development` and `python-development`. "skill-authoring" was rejected because "authoring" is a gerund.
- 2026-11-22: [agent] Dropped the old skill's mandatory 8-section template, MUST/MUST NOT modality, banned-word list, personas, and 200-600 line target. These produced padded, stilted skills. The new targets are 200 or fewer lines for SKILL.md (500 hard limit) and 300 or fewer characters for descriptions.
- 2026-11-22: [agent] The skill is model-invocable, so it loads whenever a skill is being written. The old skill was user-only, so it never triggered.
- 2026-11-22: [agent] Conventions chosen: workspace scratch in `.tmp/<skill>/`; system temp, config, and cache under an `agent-skills/<skill>/` subfolder (Unix temp: per-user `agent-skills-<uid>/<skill>/`); ephemeral names `<kind>-<YYYYMMDD-HHMMSS>[-<slug>].<ext>` (this matches `session-handoff`); stdlib Python 3.9+ as the default script language, run from source; Codex `agents/openai.yaml` sidecar for user-only skills.
- 2026-11-22: [agent] Codex review (gpt-6.2-astra) fixes: the checker validates YAML syntax and field types (with PyYAML if present, otherwise a strict subset parser), requires an effective Codex sidecar for user-only skills, fails on unresolved arguments, and handles nested fences. Unix system temp uses a per-user `agent-skills-<uid>` parent that is verified before reuse, with no `gettempdir()` working-directory fallback. `XDG_CONFIG_HOME` applies on every OS. The README shows how to run the checker from an installed skill.
- 2026-11-22: [agent] Codex round 2 fixes: the checker uses only a strict YAML subset, so results never depend on PyYAML. It rejects untyped, ambiguous, or duplicate values, checks that the sidecar policy key is a direct child, reports unreadable files as findings, and flags links that leave the skill folder. User-only skills must also say so in portable text. Unix temp parents must be `0700` on reuse, and relative env roots are ignored. The temp-storage rule is limited to workspace scratch. There is a legacy path for skills without an INTENT.md.
- 2026-11-22: [agent] Codex round 3 fixes: the checker rejects duplicate sidecar `policy` blocks, comment-only or sequence values, backslash escapes in double quotes, and uneven nesting. It requires user-only skills to say "explicitly invoke" in portable text, checks image links, and emits JSON even when no skill is found. Env roots use `Path.is_absolute()` (Windows drive-relative paths).
- 2026-11-22: [agent] Codex round 4 fixes: temp-root privacy rules (Windows inside `%USERPROFILE%`; Unix private or sticky) replace the code snippet, which now points to `session-handoff`. An existing INTENT.md is kept when building a new skill. The checker reads the user-only phrase only from the description and body, requires a Codex sidecar unless `compatibility` excludes Codex, rejects YAML-typed words and dates, accepts only an unindented closing `---`, checks `<...>` link destinations, and reports unreadable roots. Review rounds stopped here because the findings had narrowed to YAML edge cases in an advisory linter.
- 2026-11-22: [agent] Added `## Requirements` to the INTENT format, so INTENT.md captures the operator's constraints verbatim and the skill can be rebuilt from it alone. Added `scripts/check_skill.py` for the deterministic checks.
- 2026-11-22: [agent] Merged `skill-cli-development` into this skill as `references/cli.md`, during the library-wide migration to this standard. The two overlapped on script language, placement, and config paths, and disagreed on how to run scripts (`uv run` versus stdlib `python3`); this skill's rule wins. The CLI reference keeps the build-or-not table, ownership split, Lightweight and Standard tiers, config and credential rules, and footprint rules.
- 2026-11-22: [operator] "Some agent executions leave stale clones around, such as the agent-skills-review-20261122 directory. Figure out what causes these and devise a solution." [agent] Root cause: review delegation briefs cloned into the user's project folder and said to leave the clone in place, with no removal step; paths.md told skills to leave temp files in place. Added an agent scratch root (`<system-temp>/agent-skills/scratch/`) with dated names, removal at task end, and a 7-day sweep, defined in the `temp-storage` instruction.
- 2026-11-22: [agent] Codex round 1 on PR #25 (8 findings, all fixed): sweep selects by name timestamp, skips `KEEP` dirs and links, and validates the root; scratch excludes worktrees and state; uncommitted fixes are kept before removal; the no-tests advice moved to cross-harness troubleshooting; Unix uses `<scratch-root>`.
- 2026-11-22: [agent] Codex round 2 on PR #25 (6 findings, all fixed): the sweep also creates the root (private on Unix), rejects links along the whole Windows path, keeps Git checkouts with uncommitted or unpushed work, and compares full timestamps; the upstream-free check is `git log HEAD --branches --not --remotes`; troubleshooting says to report sandbox-owned folders, not escalate.
