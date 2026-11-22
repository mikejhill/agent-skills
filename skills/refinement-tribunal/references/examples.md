# Examples

## Example 1 — Refining an agent skill

**User input**: "Use refinement-tribunal on skills/test-design/SKILL.md"

**Phase 1 — Preparation**:

- Reads the file (content resolution: path with extension, file exists).
- Domain = "software testing methodology". Content type = "agent
  skill". Audience = "AI coding assistants performing test generation and
  review."
- No focus areas specified; all quality dimensions weighted equally.

**Phase 2, Iteration 1 — Tribunal Launch**:

Researcher prompt (instantiated):

> You are a world-class expert in software testing methodology with deep
> knowledge of agent skill best practices. Your task: independently
> research and report what constitutes excellence for agent skills
> intended for AI coding assistants performing test generation and review.
> \[Sections 1–5 as defined in template.] Cover both fundamental and advanced
> aspects of excellence for this content type. Prioritize depth over breadth.
> Five profound insights outweigh twenty surface observations. Do NOT reference
> or propose changes to any specific document. Report general findings only.

Harsh critic prompt (instantiated):

> You are a harsh, meticulous, and deeply knowledgeable critic specializing in
> software testing methodology. You have zero tolerance for mediocrity and an
> expert eye for agent skills. Review this agent skill and
> identify every flaw, gap, weakness, inconsistency, and missed opportunity:
> \[full skill content inserted here]. \[Sections 1–5 as defined in template.]
> This is the first review. Evaluate comprehensively across all severity levels.
> Be ruthless. Do not hedge, soften, or qualify.

Advocate prompt (instantiated):

> You are an intelligent, deeply knowledgeable, and encouraging reviewer
> specializing in software testing methodology. You have a sharp eye for what
> works well in agent skills. Review this agent skill with an
> honest but positive lens. \[full skill content inserted here]. \[Sections 1–5
> as defined in template.] This is the first review. Evaluate
> comprehensively — identify both broad and subtle strengths across the full
> content. Be honest. Do not manufacture praise.

**Phase 3, Iteration 1 — Synthesis**:

- Researcher (processed first): 12 findings total. 8 novel (novelty rate: 67%).
  Highest-impact novel finding: mutation-testing concepts not covered in the
  skill's anti-pattern catalog.
- Advocate (processed second): 4 standout strengths (protection list built), 3
  high-impact elements (amplification list built), 5 effective patterns
  identified. Greatest asset: the skill's constraint-driven structure forces
  consistent test quality.
- Harsh critic (processed third): 2 critical issues (ambiguous constraint
  language, missing edge case for framework mocking), 3 significant gaps, 5
  weaknesses, 4 minor issues. Severity score: (2 × 8) + (3 × 4) + (5 × 2) +
  (4 × 1) = 42. One significant gap targets a protected element — flagged for
  conflict resolution.
- Cross-reference: All three agents independently flagged the testing-framework
  mocking gap. Elevated to highest priority.
- Advocate-critic conflict: Harsh critic flagged "constraint language is too
  rigid" in a section the advocate identified as a standout strength
  ("constraint-driven structure"). Resolution: softened specific constraint
  language while preserving the structural pattern the advocate championed.
- Applied: 2 critical fixes, 3 gap fills, 3 novel researcher findings, 1
  advocate amplification, 2 reinforced weaknesses. Deferred: 3 weaknesses, 4
  minor items to next iteration.

**Phase 4, Iteration 1**: Counter = 1, which is less than minimum = 2. Continue
unconditionally.

**Phase 2, Iteration 2 — Tribunal Launch**:

Researcher prompt uses iteration-1 framing: "Focus exclusively on ADVANCED,
SUBTLE, and NON-OBVIOUS insights." Harsh critic reviews updated content: "Focus
on what REMAINS problematic despite prior changes." Advocate reviews updated
content: "If previously identified strengths have been weakened or removed, flag
this explicitly as STRENGTH EROSION."

**Phase 3, Iteration 2 — Synthesis**:

- Researcher: 8 findings total. 1 novel (novelty rate: 12%).
- Advocate: All 4 previously identified standout strengths preserved. 1 new
  strength emerged from prior revisions. 0 strength erosion flags.
- Harsh critic: 0 critical, 0 significant gaps, 2 weaknesses, 3 minor.
  Severity score: (0 × 8) + (0 × 4) + (2 × 2) + (3 × 1) = 7.
- Applied: deferred weaknesses from iteration 1, 2 new weaknesses, 1
  amplification from advocate, 1 novel researcher finding, 3 minor polish.

**Phase 4, Iteration 2**: Minimum met. Harsh critic: 0 critical, 0 significant
gaps. Researcher novelty rate: 12% (below 20% threshold). No strength erosion.
Severity score dropped 42 to 7 (83% decrease). STOP — 0 critical + 0
significant gaps + researcher novelty below 20%.

**Phase 5 — Delivery**: Writes updated SKILL.md, presents diff summary,
refinement log covering both iterations, and convergence rationale.

## Example 2 — Refining API Documentation with Focus Areas

**User input**:
"Use refinement-tribunal on docs/api-reference.md, focusing on developer experience"

**Orchestrator behavior**:

1. Content resolution: `docs/api-reference.md` recognized as file path (path
   separator + extension). File exists. Separate instruction extracted: focus
   areas = "developer experience".
2. Domain = "API documentation". Audience = "developers consuming the API".
   Focus dimensions mapped to: actionability, structure, completeness of
   examples.
3. Researcher prompt includes: "Prioritize the following quality dimensions
   above all others: developer experience — specifically onboarding ease,
   time-to-first-successful-call, error message clarity, and example quality.
   Weight your findings heavily toward these dimensions."
4. Harsh critic prompt includes: "Prioritize the following quality dimensions
   above all others: developer experience. Weight your critique heavily toward
   these dimensions. A flaw in a focus dimension is one severity level higher
   than it would otherwise be."
5. Advocate prompt includes: "Prioritize the following quality dimensions above
   all others: developer experience. Weight your assessment heavily toward
   strengths in these dimensions."
6. Synthesis weights focus-area findings 2× in priority ordering. For example,
   if the harsh critic flags a "weakness" in example quality (a focus
   dimension), it is treated with the same priority as a "significant gap" in a
   non-focus dimension. If the researcher independently identifies example
   coverage as a best practice and the advocate identifies existing examples as
   a standout strength, the cross-reference elevates it to highest priority
   while protecting the existing effective examples from erosion.
7. Iterates until convergence, presents diff, writes result, delivers log.
