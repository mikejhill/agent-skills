---
name: architecture-decisions
description: >-
  Create, review, and refine Architecture Decision Records (ADRs) through
  independent research, drafting, and critique, with real alternatives,
  falsifiable drivers, and concrete trade-offs. Use when the user wants an ADR
  written, reviewed, superseded, or reconstructed for a past decision.
argument-hint: "[decision topic or problem statement]"
---

# Architecture decisions

Record why a decision was made: the forces, the real alternatives, and the trade-offs accepted. The human team makes the decision; the agent researches, drafts, and critiques.

## Content rules

- One decision per ADR. If the title needs "and", split it and cross-link.
- At least two genuine options, none of them strawmen. If only one option is viable, say why, and consider whether this is a requirement rather than a decision.
- Decision drivers are specific and falsifiable: "p99 latency stays under 200 ms at current load", not "performance".
- Context states scope: which components, services, and boundaries are affected.
- Every rejected option has a reason tied to a driver. The outcome traces back to the drivers.
- Consequences name at least one good and one bad effect, each with a mechanism or metric. No "improves maintainability".
- Post-hoc ADRs reconstruct the real reasoning from history. If no formal evaluation happened, say so. Never invent rationale or list people who were not involved.
- Metadata follows the `technical-documentation` schema: decision statuses, evidence-based review, and no timestamp fields. Keep historical dates as sourced text in Context, and preserve existing records.
- Accepted content is immutable. Only lifecycle metadata (`status`, `superseded_by`) changes; a changed decision gets a new superseding ADR.
- Use the template in [adr-template.md](references/adr-template.md): the full one by default, the minimal one for low-impact decisions.

## Workflow

For an existing ADR, skip to step 6 with that ADR as the draft.

1. **Find existing ADRs** (`docs/decisions/`, `docs/adr/`, or `NNNN-*.md` files) and read them for history, numbering, and conflicts. If none exist, propose `docs/decisions/` and offer an ADR-0000 recording the adoption of ADRs.
2. **Ask for related artifacts** such as an RFC or design doc, and read them.
3. **Research** with an independent subagent using the research prompt in [prompts.md](references/prompts.md). It gets the topic only, not your opinion. For a post-hoc ADR, ask it for the historical context around the decision date.
4. **Frame the decision**: one sentence, 2-4 genuine options, and the forces that separate them. If the request hides several decisions, propose splitting. Present this to the user and get confirmation before drafting.
5. **Draft**: next free number, file `NNNN-title-with-dashes.md`, status `proposed`. Write Context first and the outcome last. Write each option's pros and cons independently. Consequences are commitments in this system, not a repeat of the pros and cons.
6. **Critique** with a second independent subagent using the critique prompt. It gets the facts from research, not your preferred option. Fix every point, or tell the user why one does not apply. Re-critique after substantial changes, three cycles at most in total.
7. **Review with the user**: the draft, the critique points addressed, and open questions. If the user rejects a critique point without a reason, raise it once more, then defer.
8. **Write the file**, and advise on next steps ([adr-guide.md](references/adr-guide.md)): who to consult, linking implementing PRs, updating superseded ADRs in the same PR, and options for a deadlocked team.

Confirm decision-makers, status, and scope with the user before marking an ADR `accepted`.

## Checklist

- [ ] Two or more genuine options, each rejection tied to a driver.
- [ ] Drivers falsifiable (full template); consequences specific, good and bad.
- [ ] One decision; scope stated; outcome traces to drivers.
- [ ] Number unused; filename lowercase and hyphenated; status `proposed` unless the user said otherwise.
- [ ] Metadata valid with no timestamps; only real participants listed.

## References

- [adr-template.md](references/adr-template.md): read when drafting. Full and minimal templates with field guidance.
- [prompts.md](references/prompts.md): read before launching the research or critique subagent.
- [adr-guide.md](references/adr-guide.md): read when advising on when to write an ADR, scoping, lifecycle, post-hoc ADRs, or team process.
- [examples.md](references/examples.md): read for annotated full, minimal, and post-hoc examples.
