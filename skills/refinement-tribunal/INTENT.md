# Intent

Bring existing text to production quality by repeatedly subjecting it to a tribunal of three independent subagents (harsh critique, advocacy, and blind research), synthesizing their findings, and revising until diminishing returns.

## Goals

1. Refined content beats what a single self-review would produce.
2. Effective elements survive iteration instead of eroding toward generic text.
3. The process stops on its own at convergence, degradation, or stagnation, and explains why.
4. Every synthesis decision is auditable.

## Requirements

- Three agents per iteration, launched in parallel: a harsh critic, an advocate, and a neutral researcher.
- Information barriers: the researcher never sees the content; the critic and advocate never see the orchestrator's views or each other's output.
- Synthesis order: researcher, then advocate (protection and amplification lists), then critic. No averaging between agents. Protected strengths change only for critical issues.
- Iterations: minimum 2, default 3, maximum 5.
- Convergence detection with a severity score, and degradation, erosion, oscillation, and stagnation checks, with rollback.
- High-capability models for subagents; inform the user and stop if none is available.
- Refines existing content only. File writes come after a diff summary.
- User-invoked only.

## Log

- 2026-11-10: Imported into the SkillSinc library layout. Requirements above are taken from the existing skill.
- 2026-11-22: [agent] Migrated to the `skill-development` standard. `SKILL.md` cut from 881 lines (over the 500 limit) to about 60; prompts, synthesis, convergence, and examples moved to `references/`. Added the portable "Run only when the user explicitly invokes it" text and the Codex `agents/openai.yaml` sidecar that user-only skills need. Dropped the persona puffery in the prompts and the rule that subagent prompts use MUST/MUST NOT modality and banned-word lists. Model names (Opus, Sonnet, `general-purpose`) were made harness-neutral.
