---
name: skill-cli-development
description: "Use when creating, modifying, or reviewing CLI tools bundled with agent skills. Covers when to build a CLI vs. use third-party tools, domain boundary design, language selection (Python preferred, Node.js when required), complexity tiers (lightweight single-file vs. standard full-project), cross-platform configuration and credential storage under ~/.config/agent-skills/, agent security boundaries, dependency and size management, testing, and maintainability standards."
---

# Skill CLI Development

## Objective

Produce CLI tools bundled with agent skills that provide deterministic, secure, and efficient domain-specific operations. CLIs act as abstraction layers between agents and underlying tools, reducing context requirements, improving execution reliability, and enforcing capability boundaries.

## Scope

**In-scope:**

- CLI tools bundled in a skill's `scripts/` directory
- Language selection and project structure
- Domain boundary design (what belongs in the CLI vs. the skill)
- Cross-platform configuration and credential storage
- Agent security boundaries and bypass prevention
- Dependency management and disk footprint
- Complexity tiers and graduation criteria
- Testing and maintainability standards

**Out-of-scope:**

- Standalone CLI tools not bundled with a skill
- Language-specific coding standards (defer to python-development, typescript-development, bash-scripting skills)
- CI/CD pipeline configuration
- Web application or library development

## Purpose

Agents already rely on CLIs for core operations: `git`, `ruff`, `eslint`, `npm`, and OS utilities. Skill CLIs extend this pattern into domains where no suitable tool exists or where existing tools are too broad, too complex, or require credentials that agents must not handle.

A skill CLI is an **API boundary**. Like any well-designed API, it reduces the surface area of decisions an agent must make:

| Benefit | How CLIs achieve it |
| --- | --- |
| **Determinism** | Fixed input/output contracts eliminate ambiguous multi-step sequences |
| **Efficiency** | One tool call replaces multiple search, read, and execute cycles |
| **Reliability** | Validated inputs and structured error handling prevent silent failures |
| **Security** | Credentials and tokens stay inside the CLI; agents never handle them |
| **Context reduction** | Agents invoke a command instead of loading domain documentation |
| **Capability extension** | CLIs provide operations agents cannot perform natively (image conversion, authenticated API calls, binary format transformations) |

## Applicability

### When to Create a CLI

- The task requires **credentials or tokens** that agents must not handle directly.
- The task involves a **multi-step sequence** that agents perform inconsistently (install tool, configure, run, parse output).
- A third-party tool exists but its interface is **too complex or too broad** for the skill's needs.
- The operation requires **environment-specific logic** (OS detection, path resolution, dependency installation).
- The agent **frequently makes errors or needs retries** for the task.

### When to Use a Third-Party CLI Directly

- The tool's interface is **simple and well-known** (e.g., `git`, `ruff`, `eslint`).
- The agent can invoke it with **predictable arguments** and parse output reliably.
- **No credentials** or environment-specific configuration is needed.
- The skill's instructions are **sufficient** to guide correct usage.

### When NOT to Create a CLI

- The task is a **single command** with no configuration or credentials.
- The operation is already handled by an **existing skill's CLI**.
- The logic can be expressed as a **one-liner** in the skill's instructions.

## Domain Boundaries

A skill CLI has a **single responsibility**: provide one cohesive domain operation through a command-line interface.

### Ownership Split

**The CLI owns:**

- Tool installation and version management
- Input validation and parameter normalization
- Credential and configuration loading
- Environment detection (OS, runtime versions, paths)
- Output formatting and error reporting
- Temporary file management and cleanup

**The skill owns:**

- When and why to invoke the CLI (decision logic)
- Input preparation (which files, which parameters)
- Output interpretation (what results mean for the task)
- Workflow orchestration (sequencing multiple CLI calls)

### Design Principles

- **Minimize parameters.** Derive values from context when possible. Fewer parameters means fewer decisions for the agent.
- **Use sensible defaults.** Every parameter must have a default that produces correct output for the common case.
- **Structured I/O.** Exit code `0` for success, non-zero for errors. Program output to stdout, diagnostics to stderr.
- **Fail loudly.** Descriptive error messages on stderr with actionable guidance. Never fail silently.
- **Isolate side effects.** File writes, network calls, and installs happen only through explicit parameters.

## Language Selection

| Priority | Language | Use when |
| --- | --- | --- |
| 1 | **Python** | Default choice. Cross-platform, strong typing, rich stdlib, fast dependency management with `uv`. |
| 2 | **Node.js** | Wrapping npm packages or when the skill's domain is JavaScript/TypeScript-centric. |
| 3 | **Bash** | Trivial wrappers (<50 lines) delegating entirely to existing CLI tools. Unix-only. |
| 4 | **PowerShell** | Windows-specific system integration with no cross-platform alternative. |

Follow the **python-development** skill for Python conventions. Follow the **typescript-development** skill for Node.js/TypeScript conventions. Follow the **bash-scripting** or **powershell-scripting** skill for shell scripts.

## Complexity Tiers

Every skill CLI belongs to one of two tiers. Choose the tier at creation time and **graduate immediately** when any threshold is crossed.

### Lightweight

A single script file in `scripts/`. Suitable for thin wrappers that delegate to an external tool.

**Characteristics:**

- Single file: `scripts/<name>.py` or `scripts/<name>.mjs`
- No build step or persistent dependency installation
- External tools invoked via `uv run --with` (Python) or `npx --yes` (Node.js)
- Self-documenting: help text in header docstring or comment block
- Argument parsing via `argparse` (Python) or manual loop (Node.js)
- No configuration files, no persistent state, no credential handling

**Limits:** ≤300 lines, ≤2 subcommands (or positional arguments only).

**Example:** The `mermaid-diagrams` skill's `scripts/mermaid-export.mjs` is a Lightweight Node.js CLI that wraps `@mermaid-js/mermaid-cli` via `npx`.

### Standard

A full project directory within `scripts/`. Required when complexity exceeds Lightweight limits.

**Characteristics:**

- Full project structure per language-skill conventions
- Build, lint, type-check, and test tooling configured
- Strictly typed code
- Automated tests
- Configuration and credential support

### Graduation Thresholds

Graduate from Lightweight to Standard **immediately** when ANY of these apply:

- Script exceeds **300 lines**
- CLI requires **persistent configuration or credentials**
- CLI has **more than 2 subcommands**
- Business logic requires **unit tests** for correctness guarantees
- External dependencies must be **installed** (beyond `npx`/`uv run --with`)

Graduation is a one-way transition. Do not revert a Standard CLI to Lightweight.

### Project Structure

**Lightweight (Python):**

```text
skills/<skill-name>/
├── SKILL.md
└── scripts/
    └── <name>.py                # #!/usr/bin/env python3
```

**Lightweight (Node.js):**

```text
skills/<skill-name>/
├── SKILL.md
└── scripts/
    └── <name>.mjs               # #!/usr/bin/env node
```

**Standard (Python):**

```text
skills/<skill-name>/
├── SKILL.md
└── scripts/<name>/
    ├── pyproject.toml            # Metadata, deps, ruff + ty config
    ├── .python-version
    ├── uv.lock
    ├── src/<package_name>/
    │   ├── __init__.py
    │   ├── __main__.py           # Entry point
    │   ├── cli.py                # argparse parsing and dispatch
    │   └── <domain>.py           # Business logic
    └── tests/
        ├── conftest.py
        └── test_<domain>.py
```

**Standard (Node.js):**

```text
skills/<skill-name>/
├── SKILL.md
└── scripts/<name>/
    ├── package.json              # Corepack packageManager, engines, bin, scripts
    ├── tsconfig.json             # strict: true, NodeNext module
    ├── biome.json                # Lint and format config
    ├── vitest.config.ts
    ├── .node-version             # Pins Node.js runtime version
    ├── src/
    │   ├── main.ts               # Entry point (bootstrap + error boundary)
    │   ├── cli.ts                # Argument parsing (node:util parseArgs)
    │   ├── errors.ts             # Error hierarchy
    │   └── <domain>.ts           # Business logic
    └── tests/
        ├── cli.test.ts
        └── <domain>.test.ts
```

## Tooling

Defer to the language-specific skill for detailed configuration. Summary:

| Concern | Python | Node.js |
| --- | --- | --- |
| Package manager | `uv` | `pnpm` (with Corepack) |
| Linting + Formatting | `ruff check` + `ruff format` | `biome check .` |
| Type checking | `ty check` | `tsc --noEmit` |
| Testing | `pytest` | `vitest` |
| Build | None (source runs directly) | `tsc` (Standard) or none (Lightweight `.mjs`) |
| Execution | `uv run` | `tsx` (Standard) or `node` (Lightweight `.mjs`) |

**Lightweight CLIs** skip formal lint, type-check, and test pipelines. Correctness is verified by manual execution.

**Standard CLIs** must pass all four checks (lint, format, type-check, test) before every commit.

### Execution Model

Skill CLIs must always run **from source** via their language's runtime management tool — never installed as standalone executables.

| Tier | Python | Node.js |
| --- | --- | --- |
| Lightweight | `uv run scripts/<name>.py` | `node scripts/<name>.mjs` |
| Standard | `uv run` (from project directory) | `npx tsx src/main.ts` |

Global or tool-level installation (`uv tool install`, `pip install`, `npm install -g`, `pnpm add -g`) creates copies that diverge from the skill's source as the skill evolves. Running from source guarantees the CLI always reflects the current skill content.

## Configuration

### Storage Location

All skill CLI configuration lives under a unified directory:

```text
~/.config/agent-skills/<skill-name>/
├── config.toml                   # User preferences and settings
└── credentials.toml              # API keys, tokens, secrets (mode 600)
```

- Use `~/.config/` as the base on **all platforms** (Windows, macOS, Linux).
- If `XDG_CONFIG_HOME` is set, use its value instead of `~/.config`.
- `<skill-name>` matches the skill's folder name (lowercase, hyphenated).

### Resolution in Code

**Python:**

```python
from pathlib import Path
import os

def config_dir(skill_name: str) -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "agent-skills" / skill_name
```

**Node.js:**

```typescript
import { join } from "node:path";
import { homedir } from "node:os";

function configDir(skillName: string): string {
  const base = process.env["XDG_CONFIG_HOME"] ?? join(homedir(), ".config");
  return join(base, "agent-skills", skillName);
}
```

### File Format

Use **TOML** for configuration and credential files. TOML supports comments, is human-editable, and aligns with the Python ecosystem (`pyproject.toml`).

For Lightweight Node.js CLIs where adding a TOML parser is disproportionate, **JSON** is acceptable.

### Rules

- **Never store defaults in config files.** Defaults belong in code. Config files override defaults only when the user explicitly sets a value.
- **Create config directory on first write, not on first run.** Do not create empty directories or files.
- **Validate config values on load.** Report invalid values with the key name, the invalid value, and the expected format.

## Security

### Credential Isolation

Agents must interact with credentials **only through CLIs**, never by reading credential files directly.

**Layered defense:**

1. **File permissions.** Set `600` (owner read/write only) on `credentials.toml` immediately after creation. On Windows, restrict the NTFS ACL to the current user.
2. **CLI design.** The CLI reads credentials internally and exposes only operation results. Credentials never appear in CLI output, logs, or error messages.
3. **Skill instructions.** The SKILL.md must explicitly instruct agents to use the CLI for authenticated operations and to never read, write, or reference credential files.
4. **Agent hooks (optional).** For high-security environments, deploy a `PreToolUse` hook that blocks file reads matching `**/credentials.toml` or `**/agent-skills/*/credentials.*`.

### Credential Setup

When a CLI requires credentials that are not yet configured:

1. The CLI detects missing credentials and exits non-zero with a message explaining what is needed and where to place it.
2. The agent reports this message to the operator.
3. The **operator** (not the agent) creates the credentials file manually.
4. The agent retries the CLI.

Agents must **never** write credential files. Credential setup is always a human-operator action.

### Bypass Prevention

Agents may attempt to bypass the CLI when it does not appear to meet their needs. To prevent this:

- **Skill instructions** must state: "Use the CLI for all \[domain\] operations. Do not invoke the underlying tool directly."
- **CLI error messages** must be actionable. If the CLI cannot perform a requested operation, state so clearly rather than failing with an opaque error.
- **Broad coverage.** Design the CLI to handle all operations the agent needs within the domain. Gaps in CLI coverage are the primary driver of bypass attempts.

## Size Management

Skills may be replicated across many repositories. Minimize disk footprint.

- **No committed dependencies.** Never commit `node_modules/`, `.venv/`, or `__pycache__/`.
- **On-demand installation.** Use `npx --yes` (Node.js) or `uv run --with` (Python) for runtime tool installation.
- **Lock files.** Standard CLIs commit lock files (`uv.lock`, `pnpm-lock.yaml`) for reproducibility. Lightweight CLIs do not use lock files.
- **No binary assets.** Do not bundle compiled binaries. Build from source or download on first run.
- **.gitignore.** Every Standard CLI directory must include a `.gitignore` excluding `node_modules/`, `.venv/`, `__pycache__/`, `dist/`, and build artifacts.

## Maintainability

### Lightweight CLIs

- Include `--help` output documenting all parameters with usage examples.
- Use descriptive variable names and section divider comments.
- Keep the script under 300 lines. If it grows, graduate to Standard.

### Standard CLIs

- All verification commands (lint, format, type-check, test) must pass before every commit.
- Document all public functions, classes, and CLI parameters.
- Include at least one test per subcommand covering the success path and one common error path.
- Pin dependency versions via lock files for reproducible builds.
- Include a `--version` flag that reports the CLI version.

## Constraints

**MUST:**

- Choose a complexity tier (Lightweight or Standard) before writing any code.
- Graduate to Standard immediately when any graduation threshold is crossed.
- Follow the language-specific skill conventions for the chosen language.
- Store configuration under `~/.config/agent-skills/<skill-name>/`.
- Set file permissions (`600`) on credential files immediately after creation.
- Include `--help` output documenting all parameters with examples.
- Use exit code `0` for success, non-zero for errors.
- Write diagnostics to stderr, program output to stdout.
- State in the parent SKILL.md that agents must use the CLI and must not bypass it.
- Use Python as the default language unless a lower-priority language is required.

**MUST NOT:**

- Commit dependencies (`node_modules/`, `.venv/`) into the skill directory.
- Expose credentials in CLI output, error messages, or logs.
- Allow agents to write credential files.
- Bundle compiled binaries in the skill directory.
- Install skill CLIs as standalone executables (`uv tool install`, `pip install`, `npm install -g`). Always run from source.
- Hard-code paths or platform-specific values without OS detection.
- Use Bash or PowerShell for CLIs requiring cross-platform support.
- Store configuration defaults in config files (defaults belong in code).

**MAY:**

- Use JSON instead of TOML for Lightweight Node.js CLI configuration.
- Skip formal linting and testing for Lightweight CLIs when manual verification is sufficient.
- Deploy agent hooks as additional enforcement for credential isolation.
