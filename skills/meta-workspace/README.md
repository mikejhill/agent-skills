# meta-workspace

Keeps work that spans several projects (plans, notes, specs, reports, and cross-project scripts) in one visible `_meta/` folder at the root of your projects folder, instead of scattering it inside individual repositories.

## Use

Loads automatically when the agent creates a document or script that is not tied to a single project. Example: "Write a plan for migrating all my projects to uv."

## Results

Files go under `<projects-root>/_meta/` in `notes/`, `specs/`, `reports/`, or `scripts/`. The agent creates `_meta/` and its `README.md` the first time.
