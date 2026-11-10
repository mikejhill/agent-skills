---
name: writing-ai-instructions
description: >-
  Author AI instruction sets (skills, instructions files, prompt files, agents)
  using structured templates with constraint modality and validation.
disable-model-invocation: true
---

# The Discipline of AI-Oriented Instruction Writing

## Objective

Produce enforceable, unambiguous instruction sets for AI agents by applying an
eight-section template with constraint modality, conflict resolution clauses,
personas, and comprehensive examples.

## Scope

### In-Scope

- Instruction writing for any Copilot feature type: agent skills, instructions
  files, prompt files, and custom agents
- The 8-section template (objective, scope, inputs, outputs, constraints,
  procedure, validation, examples) and how to apply it
- Language precision rules for AI-consumed instructions
- Constraint modality (MUST / MUST NOT / MAY)
- Conflict resolution clauses for multi-rule instruction sets
- Persona design for specialized agent behavior
- Example strategy selection (zero-shot, one-shot, few-shot) within instruction
  sets
- Validation checklists for instruction quality
- Adapting template depth by feature type and context budget

### Out-of-Scope

- Feature type selection — use the
  [copilot-features](../copilot-features/SKILL.md) skill to choose between
  skills, instructions files, prompts, agents, and hooks
- Agent hooks — hooks are JSON configuration, not instruction sets
- General prompt engineering theory (attention mechanisms, temperature,
  chain-of-thought reasoning)
- Chat-style prompting or conversational optimization
- RAG pipeline design, model fine-tuning, or training data curation

## Inputs

### Required

| Input | Description |
| --- | --- |
| **Task description** | What the instruction set must accomplish |
| **Target feature type** | Skill, instructions file, prompt file, or custom agent. If unknown, invoke the [copilot-features](../copilot-features/SKILL.md) skill first. |
| **Domain** | The subject area the instructions cover (e.g., "testing", "security", "documentation") |

### Optional

| Input | Default | Description |
| --- | --- | --- |
| **Target audience** | AI coding assistants | Who consumes the generated instructions |
| **Focus areas** | All sections equally | Sections or quality dimensions to emphasize |
| **Context budget** | No limit | Maximum token or line budget for the output |

### Assumptions

- The output will be consumed by an AI agent as part of its system context
- Markdown is the output format
- The instruction set may coexist with other instruction sets in the same agent
  context (skills, instructions files, AGENTS.md)

## Outputs

A complete instruction set in Markdown containing all applicable sections of
the 8-section template. The output is a single Markdown file (or inline
Markdown content) ready for use as a Copilot feature.

For agent skills (the most complete form), the output contains:

- Frontmatter (YAML with name, description, and optional flags)
- Objective (one sentence, verb-first)
- Scope (in-scope and out-of-scope lists)
- Inputs (required, optional, assumptions)
- Outputs (format, artifacts, naming)
- Constraints (MUST / MUST NOT / MAY rules)
- Procedure (numbered steps with decision points)
- Validation (pass conditions and failure modes)
- Examples (complete input/output demonstrations with optional personas)

For other feature types, see
[Adapting by Feature Type](#adapting-by-feature-type) for which sections to
compress or omit.

## Constraints

### Language Precision — MUST Enforce

These rules apply to every generated instruction set. The skill MUST follow
these rules in its own output, and the generated instruction set MUST
demonstrate them through its language.

**Imperative voice.** Command action. Do not suggest, recommend, or propose.

- **Use:** "Validate each input before processing."
- **Do not use:** "You should probably validate inputs."
- **Use:** "Do not modify the original file."
- **Do not use:** "Try to avoid modifying the original file."

Use imperative verbs: validate, generate, extract, verify, compute, produce,
list, declare, number.

**Eliminate vague language.** Replace soft language with concrete thresholds.

- **Vague:** "Make the output efficient."
- **Concrete:** "Output MUST process 10,000 items in under 5 seconds."
- **Vague:** "Provide a reasonable explanation."
- **Concrete:** "Explain the decision with: threat type, CVSS score, mitigation
  step."

**Banned words and replacements:**

| Banned Word | Replace With |
| --- | --- |
| "appropriate" | State the specific criterion |
| "robust" | State the resilience property (retry count, timeout, fallback) |
| "nice" / "good" | State the measurable quality (latency, accuracy, coverage) |
| "reasonable" | State the threshold or range |
| "consider" | "Evaluate X against Y" or "If X, then Y" |
| "might" / "likely" | State the condition: "If X occurs, then Y" |
| "avoid" | "Do not X" |
| "ensure" | State the specific verification step |
| "properly" | State the specific correctness criterion |
| "handle" | State the specific action: log, retry, reject, or escalate |

**Lists over prose.** Prose buries requirements; lists expose them.

- **Prose:** "The system should handle errors gracefully, logging them
  appropriately and returning a user-friendly message."
- **List:**
  - Log all errors to stderr with timestamp and stack trace.
  - Return HTTP 400 with JSON:
    `{"error": "invalid_input", "details": "[field]: [reason]"}`
  - Do not expose internal paths or system details in error messages.

**Explicit decision points.** State conditions and actions as if/then rules.

- **Weak:** "Update the config if needed."
- **Explicit:** "If existing config contains a database URL, reuse it. If not,
  ask for the database URL before proceeding."

**Constraint modality.** Mark non-negotiable rules with MUST / MUST NOT. Mark
optional behavior with MAY. Do not use SHOULD — it implies exceptions without
specifying when exceptions apply. Decompose SHOULD into conditional MUST
statements:

- **Weak:** "Functions should have docstrings."
- **Explicit:** "MUST include a docstring for every public function. MAY omit
  docstrings for private helper functions under 5 lines."

**Consistent terminology.** Define a term once, then use only that term
throughout. Do not alternate between synonyms.

**Negative space definition.** Define what something is NOT alongside what it
IS. Scope requires both in-scope and out-of-scope lists. Constraints require
both MUST and MUST NOT. Validation requires both pass and fail conditions.

**Generative specificity test.** Every rule in a generated instruction set MUST
change agent behavior beyond what an unguided agent would produce. If a rule
restates what the agent already does by default, it wastes context tokens
without adding value. Test: "Would the agent do this anyway without the rule?"
If yes, remove the rule.

### Conflict Resolution — MUST Include

When the generated instruction set contains rules that could conflict with each
other or with other instruction sets, include an explicit conflict resolution
clause.

**Structure:**

1. Declare rule priority within the instruction set:
   "If rule X and rule Y conflict, Y takes precedence."
2. Declare precedence relative to external instruction sets:
   "If this skill's constraints conflict with workspace-level instructions,
   [specify which wins]."
3. Declare a default priority hierarchy:
   Safety constraints > Correctness constraints > Style constraints.

**Include when:**

- The instruction set contains 5+ constraints, or any two constraints could
  produce contradictory instructions for the same input
- The instruction set covers a domain where safety and convenience trade off
  (security, data handling, deployment)
- The instruction set will coexist with other active instruction sets

**Example conflict resolution clause:**

```markdown
If constraints in this skill conflict with each other, resolve in this order:

1. Safety and security constraints take precedence over all others.
2. Correctness constraints take precedence over style constraints.
3. User requirements override defaults unless they violate a safety MUST or
   MUST NOT rule.
```

**This skill's own conflict resolution:**

If rules in this skill conflict with each other, resolve in this order:

1. Context budget limits take precedence over section completeness — compress or
   omit lower-priority sections rather than exceeding the budget.
2. Automation awareness takes precedence over explicit constraints — defer to
   tooling rather than restating rules.
3. Generative specificity takes precedence over thoroughness — omit rules the
   agent already follows without instruction.

### Automation Awareness — MUST Follow

If a formatter, linter, type checker, or hook already enforces a deterministic
rule (spacing, import ordering, naming conventions), reference the automation
and omit the rule text from the instruction set.

**Why:** Duplicating automation-enforced rules creates drift. When the
automation's configuration changes, the instruction text becomes contradictory.
Every rule in an instruction set MUST require non-deterministic judgment —
otherwise it belongs in tooling, not instructions.

- MUST reference the automation tool by name: "Formatting enforced by ruff (do
  not specify manually)."
- MUST NOT restate rules that tooling already guarantees.
- MAY note that automation exists in the Assumptions section.

### Context Budget — MUST Follow

Instructions compete for context window space with the agent's actual task.
Oversized instructions degrade agent performance by crowding out task-relevant
information.

Target lengths by feature type:

| Feature Type | Target Length | Rationale |
| --- | --- | --- |
| Instructions file | Under 100 lines | Always-on; every line costs tokens on every interaction |
| Prompt file | Under 150 lines | The prompt itself is the task — keep it focused |
| Agent skill | 200–600 lines | Loaded on demand when invoked |
| Complex skill with references | 600+ lines permitted | Reference materials in separate files, loaded conditionally |

This skill exceeds the agent skill target because its examples serve as both
demonstration and reference material. If a skill's examples or reference content
push it past 600 lines, extract the excess into a `references/` subdirectory
and load it conditionally. Reference files use relative Markdown links (e.g.,
`[see reference](references/example.md)`) and are loaded by the agent when it
follows the link during skill execution.

When a context budget is specified, prioritize sections in this order
(most essential first): Constraints > Procedure > Validation > Examples >
Scope > Inputs > Outputs. The Objective is never cut — it is the shortest
section and anchors everything.

**Non-obvious rationale.** For rules whose purpose is not self-evident, include
a brief parenthetical or inline explanation. This helps human maintainers
understand what would break if the rule were removed or modified, without
affecting agent execution.

## Procedure

### Adapting by Feature Type

Determine the target feature type BEFORE writing any sections. The 8-section
template is the complete form for agent skills. Different feature types require
different depth. Use this table to determine which sections to include,
compress, or omit:

| Section | Agent Skill | Instructions File | Prompt File | Custom Agent |
| --- | --- | --- | --- | --- |
| Objective | Full | 1 sentence | 1 sentence | Full |
| Scope | Full (in/out lists) | Brief or omit | Brief or omit | Full |
| Inputs | Full | Omit (always-on) | Variables only | Full |
| Outputs | Full | Omit (modifies behavior) | Full | Full |
| Constraints | Full | Full — high density | Brief | Full |
| Procedure | Full (numbered) | Omit or minimal | Numbered steps | Full |
| Validation | Full (pass/fail) | Checklist format | Brief | Full |
| Examples | 1–5 complete | 0–1 brief inline | 1–2 with variables | 1–3 |

**Key differences:**

- **Instructions files** are always-on context injected into every request.
  Maximize constraint density per line. Omit sections that add length without
  constraining behavior. Every line costs tokens on every interaction.
- **Prompt files** are user-triggered templates. Focus on the procedure and
  expected output format. Use variable interpolation (e.g., `${input}`) instead
  of a formal Inputs section.
- **Agent skills** are the most complete form. All 8 sections apply.
- **Custom agents** need identity-defining constraints, tool access
  declarations, and explicit behavioral boundaries in addition to the standard
  sections.

Each of the following eight steps produces one section of the output template.
Execute all eight steps in order. Omitting any step produces incomplete
instructions. Each step builds on the prior step's output — the sequence is a
dependency chain, not a suggestion.

Frontmatter (name, description, optional flags) is platform metadata, not a
template section. Write it after completing the 8 steps. For valid fields and
platform-specific requirements, see the
[copilot-features](../copilot-features/SKILL.md) skill.

### Step 1 — Set the Objective

Write exactly one sentence stating the measurable outcome.

- The sentence MUST begin with a verb (e.g., "Produce…", "Generate…",
  "Validate…", "Implement…").
- The sentence MUST state what the instruction set achieves, not what the agent
  does during execution.
- Do not include implementation details — those belong in the Procedure.

### Step 2 — Define Scope

- List every explicit in-scope item (what IS included).
- List every explicit out-of-scope item (what IS NOT included).
- Default scope to nothing; add only what is explicitly allowed.
- If a related skill or instruction set covers an adjacent topic, reference it
  in the out-of-scope list: "Feature type selection is out of scope — use the
  copilot-features skill."

### Step 3 — List Inputs

- Enumerate required inputs with type and format.
- Enumerate optional inputs with default values and their effect when provided.
- State all assumptions about the environment, prior state, or available
  tooling.

### Step 4 — Specify Outputs

- Prescribe exact output format (JSON, Markdown, file path, etc.).
- Name every file or artifact produced.
- Include formatting rules only when no automation enforces them; otherwise
  reference the automation and omit formatting details.

### Step 5 — State Constraints

- Declare safety and security constraints.
- Declare style, tone, and formatting constraints.
- Declare tool usage, time, and resource constraints.
- Use MUST and MUST NOT for rules; use MAY for options.
- Include a conflict resolution clause when the instruction set contains 5+
  constraints, any two constraints could conflict, or the skill will coexist
  with other instruction sets.
- Separate tooling constraints from behavioral constraints.

**Multi-mode constraints.** If the skill's domain has fundamentally different
output forms (e.g., a full project scaffold vs. a single-file script, or a
comprehensive review vs. a quick check), define named modes with separate
constraint sets for each. Share global constraints across modes; specialize
per-mode constraints only where behavior differs. Mode selection MUST be an
explicit input, not inferred by the agent.

**Tooling constraints** define what the agent can and cannot do in terms of
tools, files, and commands. Include when the task involves file I/O, command
execution, or tool access.

```markdown
Constraints:

- MUST NOT modify original source files; only provide diffs or new files.
- MUST NOT execute commands; provide them as copy-paste blocks.
- MUST reuse existing utility functions instead of reimplementing.
- MAY access read-only database backups.
```

**Environment assumptions** are declarative, not constraints. State them in the
Inputs section:

```markdown
Assumptions:

- Project uses Express.js (not Django or FastAPI).
- Secrets are managed via environment variables (not config files).
- Runtime has Node.js 18+ installed.
```

### Step 6 — Write the Procedure

Procedure writing is where most instruction sets fail. Vague steps, missing
decision points, and implicit dependencies produce instructions the agent cannot
follow reliably.

- Number every step sequentially.
- Include decision points as explicit if/then rules.
- Do not use "consider" or "think about" — command action.
- Reference specific files, functions, or artifacts — not "do the thing."
- State the dependency between steps: if Step 4 requires output from Step 2,
  say so.
- Include the expected outcome of each step (what the agent should have produced
  after completing it).

**Anti-pattern — The Vague Step:**

- Weak: "3. Set up the database."
- Strong: "3. Create the `users` table with columns: `id` (UUID primary key),
  `email` (unique, not null), `created_at` (timestamp). File:
  `migrations/001_create_users.sql`."

**Procedure template for each step:**

Each step MUST include an action verb, a specific target, and a completion
indicator. Use the pattern: "[Action verb] [specific target] [in/at location].
[Expected result or output artifact.]"

### Step 7 — Define Validation

- Specify exactly how to verify correctness.
- Include both pass conditions and failure handling.
- Name what fails the validation.
- Make every check binary (pass/fail), not qualitative ("is it clear enough?").

### Step 8 — Add Examples and Personas

#### Personas

Place the persona after the Constraints section and before the Examples section
(or, for instruction sets without examples, at the end). The persona is not one
of the 8 template sections — it is an optional enhancement that modifies how the
agent interprets the other sections.

Include a persona when the agent's worldview, decision-making framework, or
approach to the task must differ from generic competence. Test: if two equally
qualified agents would reach the same conclusion regardless of perspective, a
persona adds no value.

**Include when:**

- The task requires a specific lens (security-first, performance-aware,
  compliance-driven)
- The persona questions different assumptions than a generic agent would
- Different personas would make different tradeoff decisions on the same problem

**Exclude when:**

- The task is procedural and independent of perspective
- The persona would only change communication style, not reasoning
- Generic competence is sufficient

**Persona format:**

```markdown
Persona: [identity and background]

You are [specific identity] with [relevant experience]. You approach problems
by [characteristic method]. You prioritize [what matters most] and question
[what you scrutinize first].

When facing tradeoffs, you choose [decision priority]. You are skeptical of
[what you distrust] but trust [what you rely on].
```

**Example:**

Persona: Security-first backend architect with 12 years defending OAuth
implementations

You are paranoid about token leakage and assume every storage mechanism is
under attack until proven otherwise. You approach all design decisions by asking
"How is this encrypted at rest, in transit, and when logged?" before addressing
performance or convenience.

When facing tradeoffs, you choose security hardening over feature velocity.
You are skeptical of "we can fix it later" but trust principle-of-least-
privilege designs. You demand explicit justification for any decision that
touches credentials.

Persona details (years, titles) are illustrative; adapt them to the task.

#### Example Strategy

Select the right strategy for the instruction set's complexity:

| Task Complexity | Clarity | Strategy | Why |
| --- | --- | --- | --- |
| Simple, well-known | High | Zero-shot (no examples) | Agent knows the pattern; examples waste context |
| Medium, specific format | Medium | One-shot (1 example) | One example locks down format expectations |
| Complex, varied inputs | Low | Few-shot (2–5 examples) | Multiple examples show pattern variations and edge cases |
| Very complex, many variants | Very low | Few-shot (5+) | More examples handle edge cases but risk overfitting |

**Rules for examples:**

- Provide minimum one example per input variation.
- Examples MUST show realistic, complete input and output — not placeholders or
  ellipsis.
- Include at least one edge case or variant.
- Use consistent input/output formatting across all examples.
- Each example consumes tokens. Balance thoroughness against context budget.
- Graduated complexity (simple → medium → edge case) teaches patterns more
  effectively than random ordering.

## Validation

Apply this checklist before finalizing any instruction set. Items marked
**CRITICAL** catch errors that make the instruction set unreliable. Items marked
**IMPORTANT** improve quality. Items marked **POLISH** are refinements.

### Section Completeness

- **CRITICAL:** Objective exists — single sentence, begins with a verb, states
  measurable outcome.
- **CRITICAL:** Scope contains both an in-scope list and an out-of-scope list.
- **CRITICAL:** Constraints use MUST / MUST NOT for rules and MAY for options.
- **IMPORTANT:** Inputs enumerate required inputs with type/format, optional
  inputs with defaults, and all environment assumptions.
- **IMPORTANT:** Outputs specify exact format, name every artifact, and include
  formatting rules only when no automation enforces them.
- **IMPORTANT:** Procedure numbers steps sequentially with decision points as
  explicit if/then rules — no vague action verbs.
- **IMPORTANT:** Validation specifies both pass conditions and named failure
  modes.
- **IMPORTANT:** Examples include minimum one complete input/output per input
  variation, with at least one edge case.

### Language and Precision

- **CRITICAL:** No banned words remain ("nice," "robust," "appropriate,"
  "consider," "might," "good," "reasonable," "likely," "avoid").
- **CRITICAL:** All action verbs are imperative (validate, generate, extract,
  compute — not suggest, consider, try).
- **CRITICAL:** Every rule passes the generative specificity test — removing it
  would change agent behavior. Rules the agent already follows without
  instruction waste tokens.
- **IMPORTANT:** Threshold-based criteria where required (e.g., "process 10,000
  items in under 5 seconds," not "efficient output").
- **IMPORTANT:** All lists use bullet format — no requirements buried in prose
  paragraphs.
- **IMPORTANT:** Decision points use explicit if/then structure.
- **IMPORTANT:** Terminology is consistent throughout (same term used same way
  every time).

### Personas and Examples

- **IMPORTANT:** Personas included if task requires specific worldview or
  decision-making framework.
- **IMPORTANT:** Persona format emphasizes identity and perspective, not just
  role list (includes approach, priorities, tradeoffs).
- **IMPORTANT:** Examples are complete (not placeholders or ellipsis) with
  actual values.
- **POLISH:** Few-shot examples used for complex tasks; one-shot for format
  anchoring; zero-shot only for simple pre-trained tasks.

### Constraints and Tooling

- **CRITICAL:** Conflict resolution clause included if the instruction set
  contains 5+ constraints or will coexist with other instruction sets.
- **IMPORTANT:** Tooling constraints declared if task involves file I/O, command
  execution, or tool access.
- **IMPORTANT:** Environment assumptions stated in Inputs section, not mixed
  with constraints.
- **IMPORTANT:** No rule contradictions — if X is MUST NOT and X also appears
  as MUST, resolve explicitly.
- **POLISH:** Deterministic formatting rules omitted when automation exists;
  automation referenced instead.

### Structural Integrity

- **CRITICAL:** All required sections present (see
  [Adapting by Feature Type](#adapting-by-feature-type) for which sections
  apply to each type).
- **CRITICAL:** Every section contains substantive content — no section exists
  solely to satisfy the template. A section that restates the Objective, echoes
  the Procedure, or says "N/A" is template-filling, not instruction writing.
  Either write meaningful content or omit the section per the adaptation table.
- **IMPORTANT:** Procedure references specific files, functions, or artifacts.
- **IMPORTANT:** Validation includes both pass and fail conditions.
- **IMPORTANT:** Every MUST constraint has a corresponding validation check that
  could confirm compliance.
- **POLISH:** Examples demonstrate the same format and structure shown in the
  Outputs section.

## Examples

The following examples demonstrate three feature types. Each shows the template
adapted to the feature type's depth requirements from the
[Adapting by Feature Type](#adapting-by-feature-type) table.

### Example 1: Agent Skill — OAuth Implementation Plan (Condensed)

This is a condensed overview of the full OAuth example. For the complete
graduated three-variant demonstration (staging → production → edge-case
integration), see [references/oauth-example.md](references/oauth-example.md).

````markdown
---
name: oauth-implementation-plan
description: Produce a step-by-step plan for adding OAuth login to a Node.js API.
---

# OAuth Implementation Plan

## Objective

Produce a step-by-step implementation plan for adding OAuth login to an existing
Node.js API.

## Scope

In-scope:

- Authentication flow for selected OAuth provider
- Required endpoints, route definitions, token storage strategy
- Environment configuration and secrets management

Out-of-scope:

- UI/frontend changes
- Multi-provider OAuth support (one provider only)
- Refresh token rotation

## Inputs

Required:

- Repository path or GitHub URL
- Existing authentication middleware (code snippet or file name)
- Target OAuth provider (GitHub, Google, or Okta)

Optional:

- Preferred OAuth library (default: suggest one)
- Target deployment environment (default: staging)

## Constraints

- MUST NOT edit files; only provide code snippets and file changes.
- MUST reuse existing auth patterns in the codebase when applicable.
- MUST include security justification for token storage decisions.
- MUST specify all environment variables needed for the provider.

If constraints conflict: security justification > codebase reuse > variable
completeness.

## Procedure

1. Read existing auth modules and identify extension points.
2. If an OAuth library is already in package.json, plan around it; otherwise
   recommend one.
3. Design token storage: table schema, TTL, encrypted column strategy.
4. List all required environment variables (without secrets).
5. Write numbered implementation steps, naming specific files and functions.
6. Outline unit and integration tests.
7. Include a rollback plan (what to delete, what to revert).

## Validation

Pass: Plan includes 5+ implementation steps, all env vars documented, token
storage includes TTL and encryption, rollback plan is explicit.

Fail: Missing endpoint definitions, missing storage strategy, missing env vars,
vague rollback.

## Persona

Persona: Security-hardened backend architect

You are paranoid about token exfiltration. You approach all decisions by asking
"How does an attacker steal this?" before addressing convenience.
````

### Example 2: Instructions File — Code Review Standards

This example demonstrates the instructions file format: maximum constraint
density, no procedure, no formal inputs (always-on context).

````markdown
# Code Review Standards

Review every pull request against these standards.

## Constraints

- MUST check for security vulnerabilities before style issues.
- MUST flag any function over 50 lines as a candidate for extraction.
- MUST verify error handling exists for every external call (HTTP, database,
  file I/O).
- MUST NOT approve PRs with TODO comments in production code paths.
- MUST NOT comment on formatting — Prettier enforces formatting.
- MAY suggest performance improvements when complexity exceeds O(n²).

If security and style constraints conflict, security takes precedence.

## Validation

- [ ] Every external call has error handling
- [ ] No unresolved security findings
- [ ] No TODO comments in production paths
- [ ] Comments address substance, not formatting
````

### Example 3: Prompt File — Bug Report Triage

This example demonstrates the prompt file format: self-contained, variable
interpolation, focused on procedure and output format.

````markdown
---
mode: agent
description: Triage a bug report and produce a structured analysis.
---

# Bug Report Triage

Analyze the following bug report and produce a structured triage.

Bug report: ${input}

## Procedure

1. Identify the reported symptom (what the user observed).
2. Identify the expected behavior (what the user wanted).
3. Classify severity: P0 (data loss/security), P1 (broken feature), P2
   (degraded experience), P3 (cosmetic).
4. List reproduction steps if provided; flag "needs reproduction steps" if not.
5. Identify the most likely affected component from the codebase.
6. Recommend immediate next action.

## Output Format

| Field | Value |
| --- | --- |
| Symptom | [one sentence] |
| Expected | [one sentence] |
| Severity | [P0–P3 with justification] |
| Repro steps | [numbered list or "needs reproduction steps"] |
| Component | [file or module path] |
| Next action | [specific action verb + target] |
````

### Example 4: Custom Agent — Documentation Reviewer

This example demonstrates the custom agent format: identity-defining
constraints, tool access declarations, and behavioral boundaries.

````markdown
---
name: doc-reviewer
description: Reviews documentation for accuracy and completeness.
tools:
  - name: grep
  - name: view
  - name: glob
---

# Documentation Reviewer

You are a meticulous documentation reviewer who prioritizes technical accuracy
over stylistic polish. You verify claims against the actual codebase.

## Constraints

- MUST verify every code reference (file path, function name, CLI command)
  exists in the codebase before approving.
- MUST flag outdated version numbers or deprecated API references.
- MUST NOT modify documentation files — report findings only.
- MUST NOT review code quality; focus exclusively on documentation accuracy.
- MAY suggest structural improvements when documentation is misleading.

## Behavioral Boundaries

- Respond with a structured findings list, not prose.
- If a referenced file does not exist, classify as ERROR, not WARNING.
- If no issues are found, state "No issues found" — do not invent findings.
````

## Additional References

- [references/oauth-example.md](references/oauth-example.md) — Complete OAuth
  agent skill with three graduated input/output variants (staging, production,
  edge-case integration).
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) —
  Foundational prompt engineering concepts and best practices.
- [OpenAI GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) —
  Model-specific prompting strategies and optimization techniques.
