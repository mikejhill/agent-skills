---
name: refinement-tribunal
description: >-
  Iteratively refine existing text (docs, skills, prompts, specs, policies) to
  production quality with a parallel tribunal of three subagents: harsh
  critic, advocate, and blind researcher, until convergence. Run only when the
  user explicitly invokes it.
argument-hint: "[file path or inline text] [optional focus areas]"
disable-model-invocation: true
---

# Refinement tribunal

Run only when the user explicitly invokes it. It costs about three subagent calls per iteration on the most capable model.

Each iteration, three independent subagents review the content in parallel. You synthesize their findings, revise the content, and repeat until it converges.

| Agent | Receives | Never receives | Job |
| --- | --- | --- | --- |
| Researcher | Domain, content type, audience, iteration number | The content, your views, other agents' output | Say what excellence looks like, unanchored by the text |
| Harsh critic | Current content, domain context, iteration number | Your assessment or plans, other agents' output | Find every flaw, by severity |
| Advocate | Current content, domain context, iteration number | Your assessment or plans, other agents' output | Find strengths to protect and amplify |

The barriers are the technique. Breaking them collapses the tribunal into weaker self-review. The advocate exists because repeated harsh critique otherwise erodes voice and effective unconventional choices.

## Inputs

- **Content:** a file reference (read it; if missing, stop with "File not found: [path]. Provide the content inline or correct the path."), or about 20+ words of inline text. A short description alone is not content: ask for the text. This skill refines; it does not create from scratch.
- **Domain, content type, audience:** infer unless given.
- **Focus areas:** optional quality dimensions to weight higher.
- **Max iterations:** default 3, clamped to 2-5.

## Workflow

1. **Prepare.** Identify domain, content type, purpose, and audience. Pick the quality dimensions that matter: completeness, precision, structure, correctness, actionability, conciseness. Map focus areas onto them. Read files the content references, for the critic and advocate only. Record purpose, audience, and constraints as the **intent anchor**. Tell the user the plan: iterations, agents, and total subagent calls.
2. **Launch** the three agents in parallel on fresh subagents, using the most capable model available. If you must use a weaker model, note it in the log; if only small models are available, tell the user and stop. Prompts: [prompts.md](references/prompts.md). Never run iterations in parallel. If the harness has no subagents, tell the user the barriers cannot be enforced and ask whether to proceed with separate passes.
3. **Synthesize** in the order researcher, advocate, critic, then cross-reference, resolve conflicts, check against the intent anchor, and apply changes by priority ([synthesis.md](references/synthesis.md)). Keep the previous version for rollback. Never reintroduce an issue fixed earlier.
4. **Check convergence** after at least two iterations ([convergence.md](references/convergence.md)). Stop on convergence, the cap, degradation or erosion (revert first), oscillation, or stagnation. Otherwise go to step 2.
5. **Deliver.** For a file, show a diff summary, wait for approval where the harness allows it, then write. For inline text, return the refined text. Include the refinement log (per iteration: novelty rate, severity counts, strengths protected, conflicts and resolutions, clear-cut versus judgment-call changes) and why it stopped. Flag any unresolved critical issues.

## Done when

- At least two iterations ran, with barriers intact throughout.
- The final critique has no critical issues or significant gaps, or each is resolved or justified.
- No unresolved strength-erosion flags; no contradictions introduced.

## References

- [prompts.md](references/prompts.md): read before launching agents. The three prompt templates.
- [synthesis.md](references/synthesis.md): read at every synthesis step.
- [convergence.md](references/convergence.md): read at every convergence check, and for long content, embedded code, rollbacks, or malformed agent output.
- [examples.md](references/examples.md): read for two worked runs.
