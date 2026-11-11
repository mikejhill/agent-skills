# Prompt Engineering Evaluation Guide

## Purpose

This guide provides a comprehensive framework for evaluating and improving prompt quality. Use it to analyze prompts created for AI agents, skills, slash commands, or any AI interaction requiring reliable, high-quality outputs.

---

## Core Principles of Effective Prompts

Effective prompts share these fundamental characteristics:

1. **Precision over ambiguity** — Vague language creates variance; concrete language creates consistency
2. **Examples over explanation** — Showing expected behavior is more powerful than describing it
3. **Constraints as boundaries** — Clear rules prevent unwanted behavior
4. **Measurable outcomes** — Results can be validated objectively
5. **Appropriate complexity** — Match prompt detail to task difficulty

---

## The 8-Section Framework

Use this framework as the default for complex, high-risk, or multi-step tasks. For simple, low-risk tasks, you can use a compact prompt that covers objective, inputs, outputs, and constraints, with a single example if format adherence matters.

When you need full coverage, include these eight sections in order:

### 1. Objective

**What it is:** A single sentence stating the measurable outcome.

**Requirements:**

- Start with an action verb (generate, analyze, extract, validate, transform, etc.)
- State a specific, verifiable result
- Avoid vague outcomes like "understand" or "improve"

**Examples:**

✅ **Good:** "Extract all customer contact information from support tickets into a structured JSON format."

❌ **Bad:** "Help process customer information appropriately."

**Evaluation checklist:**

- [ ] Single sentence
- [ ] Begins with action verb
- [ ] Outcome is measurable
- [ ] No ambiguous words

---

### 2. Scope

**What it is:** Explicit boundaries defining what IS and IS NOT included.

**Requirements:**

- List all in-scope items explicitly
- List all out-of-scope items explicitly
- Assume nothing is in scope unless stated
- Address common assumptions that could mislead

**Examples:**

✅ **Good:**

```
In scope:
- Technical documentation in Markdown format
- Code examples in Python and JavaScript
- API reference documentation

Out of scope:
- User guides or tutorials
- Marketing content
- Documentation for deprecated features
- Non-English documentation
```

❌ **Bad:** "Documentation and related content"

**Evaluation checklist:**

- [ ] In-scope list is explicit and complete
- [ ] Out-of-scope list addresses likely confusion
- [ ] No implicit assumptions

---

### 3. Inputs

**What it is:** Complete specification of all required and optional inputs.

**Requirements:**

- Enumerate all required inputs with type and format
- Enumerate all optional inputs and their effects
- State all assumptions about environment or prior state
- Provide input examples

**Examples:**

✅ **Good:**

```
Required inputs:
- Source code (string, UTF-8 encoded)
- Programming language (enum: "python" | "javascript" | "typescript")
- Analysis depth (integer, 1-5 where 5 is most thorough)

Optional inputs:
- Custom rules file (JSON, schema v2.0) — if provided, overrides default rules
- Ignore patterns (array of regex strings) — excludes matching files from analysis

Assumptions:
- Source code is syntactically valid
- File paths use forward slashes (/)
- Maximum file size is 10MB
```

❌ **Bad:** "Provide the code and any settings you want to use."

**Evaluation checklist:**

- [ ] All required inputs listed with type/format
- [ ] Optional inputs listed with their effects
- [ ] Assumptions about environment stated
- [ ] Input examples provided

---

### 4. Outputs

**What it is:** Exact specification of output format, structure, and content.

**Requirements:**

- Specify exact format (JSON, Markdown, plain text, CSV, etc.)
- Name all files or artifacts produced
- Include formatting rules only when no automation enforces them; otherwise reference the formatter/linter/hook and omit formatting details
- Provide complete output examples
- Define how empty results should be represented

**Examples:**

✅ **Good:**

```
Format: JSON object with the following schema:
{
  "findings": [
    {
      "severity": "high" | "medium" | "low",
      "message": string,
      "line_number": integer,
      "column": integer
    }
  ],
  "summary": {
    "total_issues": integer,
    "high_severity_count": integer
  }
}

File naming: analysis-results-{timestamp}.json
Indentation: 2 spaces
Line length: No limit for JSON output
Empty result: {"findings": [], "summary": {"total_issues": 0, "high_severity_count": 0}}
```

❌ **Bad:** "Return the results in a useful format."

**Evaluation checklist:**

- [ ] Output format precisely specified
- [ ] File naming conventions defined
- [ ] Formatting rules stated only when no automation enforces them; automation referenced otherwise
- [ ] Complete output example provided
- [ ] Empty/null case handled

---

### 5. Constraints

**What it is:** Non-negotiable rules and boundaries for behavior.

**Requirements:**

- Use MUST for required rules
- Use MUST NOT for forbidden actions
- Use MAY for optional behaviors
- Cover safety, security, style, tone, tools, and resources
- Address potential misuse or edge cases

**Examples:**

✅ **Good:**

```
Safety & Security:
- MUST NOT execute any code submitted by users
- MUST sanitize all user input before processing
- MUST NOT expose internal file paths in error messages

Tool Usage:
- MUST use read-only file access
- MUST NOT modify original source files
- MAY create temporary files in /tmp with random names

Style & Format:
- MUST use Markdown formatting for all text output
- MUST NOT include emojis unless user explicitly requests them
- MAY use code blocks with syntax highlighting

Resource Limits:
- MUST complete analysis within 30 seconds
- MUST NOT process files larger than 10MB
```

❌ **Bad:** "Be careful with user data and try to format nicely."

**Evaluation checklist:**

- [ ] Uses MUST/MUST NOT/MAY correctly
- [ ] Covers safety and security
- [ ] Defines tool and resource limits
- [ ] Addresses style and formatting
- [ ] No vague language ("appropriate", "good", "robust")

---

### 6. Procedure

**What it is:** Step-by-step instructions for completing the task.

**Requirements:**

- Number every step sequentially
- Use imperative commands, not suggestions
- Include decision points as explicit if/then rules
- Reference specific files, functions, or artifacts by name
- Avoid "consider" or "think about" — command action instead

**Examples:**

✅ **Good:**

```
1. Parse the input source code into an abstract syntax tree (AST)
2. If parsing fails, return error with line number and syntax issue
3. If parsing succeeds, proceed to step 4
4. Walk the AST depth-first, collecting all function definitions
5. For each function definition:
   - If function has no docstring, record as severity: "medium"
   - If function has parameters but no type hints, record as severity: "low"
   - If function exceeds 50 lines, record as severity: "high"
6. Sort findings by severity (high, medium, low)
7. Generate JSON output using the schema from the Outputs section
8. Write output to file: analysis-results-{timestamp}.json
```

❌ **Bad:**

```
- Look at the code
- Consider what might be wrong
- Think about best practices
- Output your findings
```

**Evaluation checklist:**

- [ ] Steps are numbered sequentially
- [ ] All steps use imperative voice
- [ ] Decision points are explicit if/then rules
- [ ] No vague verbs ("consider", "think", "maybe")
- [ ] References specific artifacts by name

---

### 7. Validation

**What it is:** Explicit criteria for verifying success or failure.

**Requirements:**

- Define pass conditions objectively
- Define failure conditions explicitly
- Specify how to handle failures
- Include edge case validation
- Provide testing criteria

**Examples:**

✅ **Good:**

```
Pass conditions:
- Output file exists and is valid JSON
- All findings include severity, message, line_number, and column
- summary.total_issues equals the count of findings array
- Execution completes within 30 seconds
- No exceptions or errors logged

Failure conditions:
- Input file does not exist → Return error: "File not found: {path}"
- Input file is not valid Python → Return error: "Syntax error at line {n}: {message}"
- Input file exceeds 10MB → Return error: "File too large: {size}MB (max 10MB)"
- Analysis timeout after 30s → Return partial results with warning
- Invalid JSON output → Log error and retry with simplified findings

Edge cases:
- Empty file → Return zero findings, total_issues: 0
- File with only comments → Return zero findings, total_issues: 0
- File with syntax errors → Return error, do not attempt analysis
```

❌ **Bad:** "Make sure the output looks good and doesn't have errors."

**Evaluation checklist:**

- [ ] Pass conditions are objective and measurable
- [ ] Failure conditions are named and handled
- [ ] Edge cases are addressed
- [ ] Error messages are specific
- [ ] No subjective criteria ("good", "appropriate")

---

### 8. Examples

**What it is:** Complete demonstrations showing inputs and expected outputs.

**Requirements:**

- Include minimum one example per input variation
- Show realistic, complete inputs and outputs
- Demonstrate edge cases
- Use consistent formatting
- Label examples clearly

**Strategy selection:**

- **Zero-shot** (no examples): Use only for simple, well-known tasks where format is obvious
- **One-shot** (1 example): Use to anchor format and style for straightforward tasks
- **Few-shot** (2-5 examples): Use for complex tasks with multiple input variations
- **Many-shot** (5+ examples): Use for very complex tasks with many edge cases

**Examples:**

✅ **Good (Few-shot):**

````
Example 1: Simple function without docstring

INPUT:
```python
def calculate_total(items):
    return sum(items)
```

OUTPUT:

```json
{
  "findings": [
    {
      "severity": "medium",
      "message": "Function 'calculate_total' missing docstring",
      "line_number": 1,
      "column": 0
    },
    {
      "severity": "low",
      "message": "Parameter 'items' missing type hint",
      "line_number": 1,
      "column": 20
    }
  ],
  "summary": {
    "total_issues": 2,
    "high_severity_count": 0
  }
}
```

Example 2: Empty file

INPUT:

```python
# (empty file)
```

OUTPUT:

```json
{
  "findings": [],
  "summary": {
    "total_issues": 0,
    "high_severity_count": 0
  }
}
```

Example 3: Long function with all issues

INPUT:

```python
def process_data(data, config, options):
  # 60 lines of code omitted for brevity in this example
  return result
```

OUTPUT:

```json
{
  "findings": [
    {
      "severity": "high",
      "message": "Function 'process_data' exceeds 50 lines (60 lines)",
      "line_number": 1,
      "column": 0
    },
    {
      "severity": "medium",
      "message": "Function 'process_data' missing docstring",
      "line_number": 1,
      "column": 0
    },
    {
      "severity": "low",
      "message": "Parameter 'data' missing type hint",
      "line_number": 1,
      "column": 17
    }
  ],
  "summary": {
    "total_issues": 3,
    "high_severity_count": 1
  }
}
```
````

❌ **Bad:**

```
Example:
Give it some code and it will analyze it.
```

**Evaluation checklist:**

- [ ] Includes 1+ examples per major input variation
- [ ] Shows complete, realistic inputs and outputs
- [ ] Includes edge cases
- [ ] Examples use same format as specified in Outputs
- [ ] No placeholders or ellipsis (...)

---

## Language and Style Rules

Apply these rules when writing or evaluating any prompt:

| Rule                             | ✅ Do This                                                                            | ❌ Not This                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Use imperative voice**         | "Validate each input before processing."                                              | "You should probably validate inputs."                          |
| **Eliminate vague language**     | "Process 10,000 items in under 5 seconds."                                            | "Make the output efficient."                                    |
| **Prefer lists over prose**      | Bulleted requirements list                                                            | Paragraph of requirements                                       |
| **Use explicit conditionals**    | "If X, then Y. If not X, then Z."                                                     | "Handle X appropriately."                                       |
| **Ban ambiguous words**          | Never use: "appropriate", "nice", "robust", "good", "reasonable", "consider", "might" | Use: measurable criteria, specific thresholds, concrete actions |
| **Use MUST/MUST NOT/MAY**        | "MUST validate", "MUST NOT execute", "MAY cache"                                      | "Should validate", "Try not to execute", "Can cache"            |
| **Be specific about format**     | "Return JSON with keys: name, email, phone"                                           | "Return the data in a structured format"                        |
| **Define edge cases explicitly** | "If input is empty, return []"                                                        | "Handle unusual inputs gracefully"                              |

---

## Personas: When and How

**Include a persona when:**

- The task requires a specific expertise or worldview
- Different perspectives would make different decisions
- The persona changes reasoning, not just communication style
- Security, compliance, or domain expertise is critical

**Persona structure:**

```markdown
Persona: [specific identity with experience]

You are [identity] with [years/background]. You approach problems by [method].
You prioritize [values] and question [skeptical-of] first.

When facing tradeoffs, you choose [priority]. You distrust [what-you-doubt]
but trust [what-you-rely-on].
```

**Example:**

✅ **Good:**

```
Persona: Security-first backend architect with 10 years defending production systems

You are paranoid about data exposure and assume every input is malicious until
proven otherwise. You approach all design decisions by asking "How does an
attacker exploit this?" before considering performance or convenience.

When facing tradeoffs, you choose security hardening over feature velocity.
You distrust client-side validation and convenience functions, but trust
principle-of-least-privilege and defense-in-depth.
```

❌ **Bad:**

```
Persona: You are a helpful security expert who knows about backend systems.
```

**Evaluation checklist:**

- [ ] Persona includes identity and experience
- [ ] Describes characteristic approach/method
- [ ] States clear priorities and tradeoffs
- [ ] Defines what the persona distrusts vs. trusts
- [ ] Changes reasoning, not just tone

---

## Advanced Techniques

### In-Context Learning (Few-Shot Prompting)

The number and quality of examples directly determines output quality:

| Task Type                     | Example Count  | Rationale                                |
| ----------------------------- | -------------- | ---------------------------------------- |
| Simple, well-known            | 0 (zero-shot)  | Model already knows the pattern          |
| Specific format needed        | 1 (one-shot)   | Locks down format expectations           |
| Complex, varied inputs        | 2-5 (few-shot) | Shows pattern variations and edge cases  |
| Very complex, many edge cases | 5+ (many-shot) | Handles complexity but risks overfitting |

**Example quality matters more than quantity:**

- Show diverse inputs, not similar ones
- Include edge cases, not just happy paths
- Demonstrate exact output format
- Use realistic data, not simplified examples

### Prompt Chaining

Break complex tasks into sequential prompts where each prompt's output feeds the next:

```
Prompt 1: Extract entities → Output: List of entities
Prompt 2: Classify entities → Output: Categorized entities
Prompt 3: Generate summary → Output: Final report
```

**When to use:**

- Task is too complex for a single prompt
- Intermediate validation is needed
- Different expertise needed at each step
- Debugging needs to identify which step failed

### Chain-of-Thought (CoT)

Prefer asking for concise rationale or decision criteria rather than full step-by-step reasoning. Reserve explicit chain-of-thought requests for debugging or research scenarios where the reasoning process itself is the product.

```
Provide your final answer first. Then give a brief rationale in 2-4 bullet points.
```

**When to use:**

- Complex reasoning or multi-step logic where brief rationale is sufficient
- Need to verify decision criteria without verbose reasoning
- Task requires transparency or explainability with short justifications
- Debugging incorrect outputs (use explicit step-by-step reasoning only here)

### ReAct (Reasoning + Acting)

Combine reasoning with tool use in an iterative loop:

```
1. Think: What do I need to do next?
2. Act: Call a tool or take action
3. Observe: Review the result
4. Repeat until task is complete
```

**When to use:**

- Agent-based systems
- Tasks requiring external tools or APIs
- Multi-step problem-solving
- Dynamic environments

---

## Common Prompt Anti-Patterns

### ❌ Anti-Pattern 1: Vague Success Criteria

**Problem:**

```
"Provide a good analysis of the code with useful suggestions."
```

**Why it fails:** "Good" and "useful" are subjective. Every run produces different output.

**Fix:**

```
Analysis must include:
- Cyclomatic complexity score for each function
- Functions exceeding 10 parameters (list with line numbers)
- Unused imports (list with file paths)
- Code duplication (blocks of 5+ identical lines)

Format as JSON with keys: complexity_scores, parameter_violations, unused_imports, duplications
```

---

### ❌ Anti-Pattern 2: Buried Requirements

**Problem:**

```
The system should analyze the code and handle errors gracefully, logging them
appropriately and returning user-friendly messages while also checking for
security issues and performance problems.
```

**Why it fails:** Requirements hidden in prose are easy to miss. The model may skip some.

**Fix:**

```
Requirements:
- Analyze code for security vulnerabilities
- Analyze code for performance issues
- Log all errors to stderr with timestamp and stack trace
- Return HTTP 400 with JSON: {"error": "invalid_input", "details": "[reason]"}
- Never expose internal paths in error messages
```

---

### ❌ Anti-Pattern 3: Implicit Conditionals

**Problem:**

```
"Update the configuration if needed."
```

**Why it fails:** "If needed" is ambiguous. Model must guess the condition.

**Fix:**

```
If existing config contains database_url key:
  - Reuse existing database_url value
  - Do not prompt user
If existing config does not contain database_url key:
  - Prompt user: "Enter database URL: "
  - Validate URL format matches: postgresql://[user]:[pass]@[host]:[port]/[db]
  - Add database_url to config
```

---

### ❌ Anti-Pattern 4: Missing Edge Cases

**Problem:**

```
"Extract email addresses from the text."
```

**Why it fails:** Doesn't specify what to do with malformed emails, duplicates, or empty input.

**Fix:**

```
Extract email addresses from the text.

Rules:
- Email must match pattern: [local]@[domain].[tld]
- If email is malformed, skip it (do not include in results)
- If duplicate emails found, include only first occurrence
- If no emails found, return empty array: []
- If input text is empty or null, return empty array: []

Output format: JSON array of strings
Example: ["user@example.com", "admin@example.org"]
```

---

### ❌ Anti-Pattern 5: Negative Instructions

**Problem:**

```
"Do not ask for personal information. Do not ask about interests."
```

**Why it fails:** Telling the model what NOT to do doesn't guide it to what it SHOULD do.

**Fix:**

```
Recommend a movie from the top 10 global trending movies.

Rules:
- MUST select from current top 10 trending list
- MUST NOT ask user for preferences or interests
- MUST NOT request personal information
- If no suitable movie found, respond: "Sorry, no movie recommendation available today."

Example response: "I recommend 'The Stellar Journey' — currently #3 on global trending."
```

---

## Evaluation Scoring Rubric

Use this rubric to score prompts on a scale of 1-5 for each dimension:

### Completeness (Are all 8 sections present?)

| Score | Criteria                                                |
| ----- | ------------------------------------------------------- |
| 5     | All 8 sections present, complete, and well-developed    |
| 4     | All 8 sections present, minor gaps in detail            |
| 3     | 6-7 sections present OR all present but several weak    |
| 2     | 4-5 sections present OR major gaps in critical sections |
| 1     | 3 or fewer sections present, prompt is skeletal         |

### Precision (Is language concrete and unambiguous?)

| Score | Criteria                                                             |
| ----- | -------------------------------------------------------------------- |
| 5     | Zero vague words, all criteria measurable, all conditionals explicit |
| 4     | 1-2 minor ambiguities, otherwise precise                             |
| 3     | Several vague terms but core meaning clear                           |
| 2     | Significant ambiguity in requirements or outputs                     |
| 1     | Pervasively vague language, no concrete criteria                     |

### Structure (Is information logically organized?)

| Score | Criteria                                                     |
| ----- | ------------------------------------------------------------ |
| 5     | Perfect logical flow, easy to follow, uses lists effectively |
| 4     | Good structure, minor organizational issues                  |
| 3     | Understandable but could be better organized                 |
| 2     | Confusing organization, buried requirements                  |
| 1     | Chaotic, no clear structure                                  |

### Examples (Are examples complete and helpful?)

| Score | Criteria                                                      |
| ----- | ------------------------------------------------------------- |
| 5     | Multiple complete examples covering variations and edge cases |
| 4     | 1-2 complete examples, covers main cases                      |
| 3     | Examples present but incomplete or simplified                 |
| 2     | Minimal examples or placeholders only                         |
| 1     | No examples provided                                          |

### Validation (Can success/failure be verified?)

| Score | Criteria                                                               |
| ----- | ---------------------------------------------------------------------- |
| 5     | Clear pass/fail criteria, edge cases handled, error messages specified |
| 4     | Good validation criteria, minor gaps                                   |
| 3     | Basic validation described, some ambiguity                             |
| 2     | Vague validation, hard to verify objectively                           |
| 1     | No validation criteria provided                                        |

### Overall Prompt Quality

Calculate average score across all five dimensions:

- **4.5-5.0:** Production-ready, exemplary quality
- **3.5-4.4:** Solid prompt, minor improvements recommended
- **2.5-3.4:** Functional but needs significant refinement
- **1.5-2.4:** Major issues, requires substantial rework
- **1.0-1.4:** Not usable, start over with framework

---

## Practical Evaluation Workflow

### Step 1: Initial Scan

Read the prompt once and note:

- [ ] Are all 8 sections present?
- [ ] Is the objective clear?
- [ ] Are there examples?
- [ ] Can I understand what success looks like?

### Step 2: Language Audit

Search for banned words and vague language:

- "appropriate", "nice", "robust", "good", "reasonable", "consider", "might", "likely"
- "should", "could", "try to", "please"
- "efficiently", "properly", "correctly" (without defining the standard)

**For each occurrence:** Replace with concrete, measurable criteria.

### Step 3: Section-by-Section Review

Use the checklists provided in each section above to verify:

- Objective: Single sentence, action verb, measurable
- Scope: Explicit in/out of scope lists
- Inputs: All inputs typed, formats specified
- Outputs: Exact format, examples provided
- Constraints: MUST/MUST NOT/MAY used correctly
- Procedure: Numbered steps, imperative voice, explicit decisions
- Validation: Pass/fail criteria, error handling
- Examples: Complete, realistic, covers edge cases

### Step 4: Test Against Edge Cases

Ask:

- What happens with empty input?
- What happens with malformed input?
- What happens if a resource is unavailable?
- What happens if processing takes too long?
- What happens with maximum-size input?

**Each edge case should be explicitly handled in the prompt.**

### Step 5: Score and Recommend

Use the rubric above to:

1. Score each dimension (1-5)
2. Calculate average
3. List top 3 improvements needed
4. Provide specific revision recommendations

---

## Example Evaluation

**Prompt to evaluate:**

```
Analyze the code and tell me what's wrong with it.
```

**Evaluation:**

| Dimension    | Score     | Reason                                          |
| ------------ | --------- | ----------------------------------------------- |
| Completeness | 1/5       | Missing all 8 sections except implied objective |
| Precision    | 1/5       | "wrong with it" is completely subjective        |
| Structure    | 1/5       | No structure, single sentence                   |
| Examples     | 1/5       | No examples                                     |
| Validation   | 1/5       | No criteria for success                         |
| **Overall**  | **1.0/5** | Not usable                                      |

**Top 3 improvements:**

1. Define "what's wrong" with specific, measurable criteria (e.g., syntax errors, security issues, style violations)
2. Specify output format and structure (JSON, Markdown, plain text?)
3. Provide complete examples showing input code and expected analysis output

**Revised prompt snippet:**

```
Objective: Identify security vulnerabilities and code quality issues in Python source code.

Scope:
In scope:
- SQL injection vulnerabilities
- Hardcoded credentials
- Unused imports
- Functions exceeding 50 lines

Out of scope:
- Performance optimization
- Style preferences (PEP 8)
- Documentation quality

[... continue with all 8 sections ...]
```

---

## Quick Reference Checklist

Use this for rapid evaluation:

**Structure:**

- [ ] All 8 sections present
- [ ] Sections in correct order
- [ ] Lists used instead of prose

**Language:**

- [ ] No vague words (appropriate, good, robust, etc.)
- [ ] MUST/MUST NOT/MAY used correctly
- [ ] Imperative voice throughout
- [ ] No "consider" or "think about"

**Content:**

- [ ] Objective is measurable
- [ ] Inputs are typed and formatted
- [ ] Outputs have complete examples
- [ ] Constraints cover safety and tools
- [ ] Procedure has numbered steps
- [ ] Validation defines pass/fail
- [ ] Examples show edge cases

**Quality:**

- [ ] Can execute without guessing
- [ ] Edge cases explicitly handled
- [ ] Success criteria are objective
- [ ] Failures have specific error messages

---

## References and Further Reading

### Foundational Resources

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)

### Technique References

- [Chain-of-Thought Prompting](https://www.promptingguide.ai/techniques/cot)
- [ReAct: Reasoning and Acting](https://www.promptingguide.ai/techniques/react)
- [Tree of Thoughts](https://www.promptingguide.ai/techniques/tot)
- [Retrieval Augmented Generation](https://www.promptingguide.ai/techniques/rag)

### Academic Papers

- Wei et al. (2022): "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- Yao et al. (2023): "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
- Zhou et al. (2023): "Large Language Models Are Human-Level Prompt Engineers"

---

## Version History

- **v1.0.0** (2026-02-10): Initial release with 8-section framework, evaluation rubric, and comprehensive examples

---

## License

This resource is part of the agent-skills repository and follows the same license terms.
