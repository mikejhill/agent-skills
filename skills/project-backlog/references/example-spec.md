# Project Template Generator

## Problem / Purpose

Starting a new project requires assembling boilerplate: directory
structures, configuration files, CI workflows, linting rules, and
documentation scaffolding. This work is repetitive, error-prone, and
inconsistent across projects. Developers either copy from an existing
project (inheriting its quirks) or start from scratch (missing established
patterns).

A project template generator solves this by producing complete, consistent
project scaffolding from predefined templates. It encodes organizational
standards into reusable templates so that every new project starts from
a proven foundation.

## Scope

### In-Scope

- CLI tool that generates project scaffolding from templates
- Template system supporting multiple languages and project types
- Interactive and non-interactive (flag-driven) modes
- Configuration file for user-level defaults (e.g., author name, license
  preference)
- Built-in templates for Python, TypeScript, and shell script projects
- Post-generation hooks for running setup commands (e.g., `git init`,
  `npm install`)

### Out-of-Scope

- IDE integration or GUI — this is a CLI-only tool
- Template hosting or registry — templates ship with the tool or are
  loaded from local directories
- Ongoing project management after generation — this tool creates the
  initial scaffolding only

## Goals

- A new Python, TypeScript, or shell project can be scaffolded in under
  30 seconds with all standard configuration in place.
- Generated projects pass linting and build on first run without manual
  fixes.
- Adding a new template requires only creating a template directory with
  a manifest file — no code changes to the generator itself.
- The tool runs on Windows, macOS, and Linux without platform-specific
  installation steps.

## Use Cases

### New Python Library

A developer runs `tmpl create --type python-lib --name my-library` and
receives a complete project directory with `pyproject.toml`, `src/`
layout, `tests/` directory, GitHub Actions workflow, `.gitignore`, and
a README. The project is ready for `pip install -e .` and `pytest`
immediately.

### Custom Template

A team lead creates a `templates/django-api/` directory with their
organization's standard Django project layout and a `template.yaml`
manifest. Any team member can now run `tmpl create --type django-api`
to generate a project matching team standards.

### Non-Interactive CI Usage

A CI pipeline runs `tmpl create --type python-lib --name test-project
--defaults` to generate a project for integration testing. The
`--defaults` flag skips all prompts and uses configured defaults.

## Requirements and Constraints

- Must be distributed as a single installable package (pip or standalone
  binary).
- Must not require network access at generation time — all templates are
  local.
- Template rendering must support variable substitution (project name,
  author, date, license) but must not execute arbitrary code during
  generation.
- Generated projects must not contain references to the template generator
  itself — the output is a standalone project.
- Must preserve file permissions from templates (especially executable
  scripts).

## Proposed Design

### Architecture

The generator consists of three components:

1. **CLI Frontend** — Parses arguments, runs interactive prompts, invokes
   the engine. Built with `click`.
2. **Template Engine** — Reads template directories, resolves variables,
   renders output. Uses Jinja2 for text substitution with a restricted
   environment (no arbitrary code execution).
3. **Hook Runner** — Executes post-generation commands defined in the
   template manifest (e.g., `git init`, `npm install`).

### Template Format

Each template is a directory containing:

```
templates/<template-name>/
├── template.yaml          # Manifest: variables, defaults, hooks
├── {{project_name}}/      # Output directory (name is a template)
│   ├── README.md          # Files with Jinja2 variable placeholders
│   ├── pyproject.toml
│   └── src/
│       └── __init__.py
```

The `template.yaml` manifest defines:

```yaml
name: python-lib
description: Python library with src layout
variables:
  project_name:
    prompt: "Project name"
    required: true
  author:
    prompt: "Author name"
    default: "{{ user.name }}"
  license:
    prompt: "License"
    default: "MIT"
    choices: ["MIT", "Apache-2.0", "BSD-3-Clause"]
hooks:
  post_generate:
    - "git init"
    - "git add ."
```

### Configuration

User-level defaults are stored in `~/.config/tmpl/config.yaml`:

```yaml
defaults:
  author: "Jane Smith"
  license: "MIT"
template_dirs:
  - "~/templates"
  - "/org/shared-templates"
```

## Cross-Cutting Concerns

### Security

Templates must not execute arbitrary code during rendering. The Jinja2
environment is sandboxed: no `import`, no `eval`, no file system access.
Post-generation hooks are listed explicitly in `template.yaml` and
displayed to the user before execution in interactive mode.

### Compatibility

Must run on Python 3.10+ across Windows, macOS, and Linux. File path
handling uses `pathlib` exclusively. Line endings are preserved as-is
from templates (no automatic conversion).

### Usability / Developer Experience

- Interactive mode guides users through all variables with defaults shown.
- Non-interactive mode accepts all variables as CLI flags.
- `tmpl list` shows available templates with descriptions.
- Error messages include the template file and line number when rendering
  fails.

### Testing Strategy

- Unit tests for the template engine (variable resolution, rendering,
  sandboxing).
- Integration tests that generate each built-in template and verify the
  output passes linting and builds.
- Snapshot tests comparing generated output against expected baselines.

## Risks and Trade-offs

- **Jinja2 sandboxing is not a security boundary.** The sandbox prevents
  accidental code execution but is not hardened against adversarial
  templates. Mitigation: templates are locally authored and trusted.
- **No remote template support.** Users must manage template distribution
  themselves. This keeps the tool simple and offline-capable, at the cost
  of manual template sharing.
- **Variable substitution in filenames.** Jinja2 syntax in directory and
  file names (`{{project_name}}`) can confuse some file system tools.
  Mitigation: the generator resolves these before writing; they never
  appear in the output.

## Open Questions

- Should the tool support template inheritance (a base template that
  others extend)?
- Should generated projects include a `.tmpl-origin` file recording which
  template and version was used?

## Alternatives Considered

### Cookiecutter

Mature Python-based template generator with a large ecosystem. Rejected
because it executes arbitrary Python hooks during generation (security
concern), its Jinja2 environment is not sandboxed, and its template format
is more complex than needed for this use case.

### Copier

Modern Python template tool with update/migration support. Rejected
because the migration feature adds complexity that is out of scope — this
tool is for initial scaffolding only, not ongoing template sync.

## References

- [Jinja2 Sandbox](https://jinja.palletsprojects.com/en/3.1.x/sandbox/)
- [Cookiecutter documentation](https://cookiecutter.readthedocs.io/)
- [Copier documentation](https://copier.readthedocs.io/)
