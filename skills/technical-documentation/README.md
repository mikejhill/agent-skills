# technical-documentation

Standards for writing clear technical documents (procedures, specs, reports, explanations) and for organizing a project's documentation: `docs/` layout, README indexes, single sources of truth, and lifecycle metadata.

## Use

Loads automatically when the agent writes or reviews documentation in any format, or organizes a docs folder. Examples:

- "Write a runbook for rotating the API keys."
- "Reorganize our docs folder."

## Results

Documents lead with the key point, use steps, bullets, and tables over long prose, and never claim reviews or test runs that did not happen. Docs that need lifecycle tracking get YAML frontmatter, validated by `assets/metadata.schema.json`.
