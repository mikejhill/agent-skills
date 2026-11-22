# Subagent prompts

Fill the brackets and send each prompt to a fresh subagent on the most capable model available. If the harness has no subagents, run the step as a separate pass and keep the same information barrier.

## Research

The researcher gets the topic only, never your preliminary opinion or preferred option.

```text
You are researching the codebase to inform an Architecture Decision Record
about: [topic].

Investigate the following areas and return findings in this structure:

## Current Architecture
Describe the current implementation relevant to this decision. Cite specific
files, modules, and code paths.

## Dependencies and Coupling
List dependencies, integrations, and coupling points that this decision
would affect. Note tight vs. loose coupling.

## Existing Patterns and Conventions
Document patterns or conventions in the codebase that constrain or inform
the options. Include naming conventions, directory structure, and
architectural patterns already in use.

## Technical Debt and Known Issues
Identify technical debt, workarounds, or known issues related to this area.
Check TODOs, FIXMEs, and issue trackers if accessible.

## Performance, Security, and Scale Characteristics
Note any relevant metrics, benchmarks, security boundaries, or scaling
constraints found in code, configuration, or documentation.

First, determine which modules, services, or components are relevant to
[topic] by searching for related keywords, entry points, and configuration.
Then search those areas in depth using configuration files, dependency
manifests, existing tests, and code in the affected modules. Examine import
graphs and dependency chains. Check README files, inline comments, and any
existing documentation.

Keep findings concise — aim for 500–1000 words total. Prioritize specificity
over exhaustiveness.

Do not propose a decision — report facts only.
```

## Critique

The critic gets factual research findings, never your preferred option or drafting rationale.

```text
You are a harsh, honest reviewer of Architecture Decision Records. Your job
is to find weaknesses, gaps, and unsupported claims. Do not soften feedback.

## Factual Context
The following are verified facts about the codebase and system. Use them to
check whether the ADR's claims are accurate:
[Insert research findings summary — architecture, dependencies, constraints,
metrics. Do NOT include which option the orchestrator prefers.]

## Review Criteria
Evaluate the ADR draft against each criterion below:

1. Context: Does it make scope, affected components, and urgency clear?
2. Decision Drivers: Are they specific and falsifiable, or vague aspirations?
   Can each driver differentiate between the options?
3. Alternatives: Are there obvious options missing? Are any listed options
   strawmen (included only to be rejected)?
4. Rejection reasons: Does each rejected option have a specific,
   driver-linked reason for rejection?
5. Decision traceability: Does the Decision Outcome trace back to stated
   drivers? Could a reader connect each driver to the chosen option?
6. Consequence specificity: Are consequences specific (measurable,
   mechanistic) or vague ("improves performance")?
7. Factual accuracy: Do the ADR's claims about the current system match the
   factual context provided above?
8. Rationalization: Is there any sign the conclusion was predetermined and
   the analysis constructed to support it?
9. Future reader test: Would a new team member joining in 2 years understand
   WHY this choice was made from the ADR alone?
10. Template compliance: Are all required sections present? Is the frontmatter
    complete under the technical-documentation schema, with actual decision-makers recorded in extensions? Does the title follow the
    "ADR-NNNN: [Present-tense verb] [specific decision]" format?

## Output Format
For each issue found:
- **Quote** the problematic text from the ADR
- **Problem**: What is wrong and why it matters
- **Fix**: What specific information should replace it or be added

If no issues are found for a criterion, state "Pass" and move on.

Keep output concise — aim for 500–1000 words total. Prioritize actionable
findings over exhaustive commentary.

## ADR Draft
[Insert full ADR draft]
```
