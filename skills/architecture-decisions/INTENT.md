# Intent

Produce well-researched Architecture Decision Records with documented alternatives, clear rationale, and actionable consequences, through independent research and critique. Renamed from `adr-generation`.

## Goals

1. A reader two years later understands why the choice was made from the ADR alone.
2. Alternatives and trade-offs are real, specific, and traceable to drivers.
3. Research and critique are independent of the drafter's preferences.
4. ADRs stay honest: no invented rationale, participants, or verification.

## Requirements

- Create, review, and refine ADRs; advise on scope, splitting, merging, and lifecycle; support post-hoc ADRs.
- The human team makes the decision. The agent presents drafts for review and confirms decision-makers, status, and scope before acceptance.
- At least two considered options; specific, falsifiable drivers; at least one good and one bad consequence; driver-linked rejection reasons; one decision per ADR.
- Multi-agent workflow: research subagent, drafting, critique subagent, refinement, user review. Subagents do not receive the orchestrator's preferred option. At most three critique cycles.
- Research existing ADRs before drafting.
- Metadata follows the project documentation schema, with no timestamp fields; historical chronology is preserved as sourced text.
- File names `NNNN-title-with-dashes.md`, default directory `docs/decisions/`.
- Out of scope: making the decision, implementing it, ADR tooling and publishing.

## Log

- 2026-11-10: Imported into the SkillSinc library layout as `adr-generation`. Requirements above are taken from that skill.
- 2026-11-22: [agent] Renamed to `architecture-decisions` during the migration to the `skill-development` standard: a subject name that covers creating, reviewing, and refining. Cut `SKILL.md` from 313 to about 70 lines. The subagent prompts moved to `references/prompts.md`, and the persona and MUST/MAY lists were dropped. Harness-specific subagent wording (agent type names, model tiers) was made neutral. Metadata references now point to `technical-documentation`.
- 2026-11-22: [agent] Codex review fixes on the migration: reviewing an existing ADR returns findings only and runs fact research first when the code is at hand.
- 2026-11-22: [agent] Removed named references to other skills and instruction files; adjacent concerns are now described by capability ("any ... standards the user has") so the skill stands alone.
