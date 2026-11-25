# meta-workspace

Makes `_meta/` at the root of your projects folder the default home for documents, reports, notes, specs, scripts, and other transient files that agents generate, so they stop landing inside repositories or scattered across your disk.

## Use

Loads automatically when the agent creates a document, report, note, spec, script, or supporting file that does not belong in a project's own files or a location you named. Example: "Write a report on outdated dependencies across my projects."

## Results

Files go under `<projects-root>/_meta/` in `files/`, `notes/`, `reports/`, `scratch/`, `scripts/`, or `specs/`. Every file and subfolder is named `YYYY-MM-DD-<label>`, so you can see at a glance how old it is and clear out stale items. The agent creates `_meta/` and its `README.md` the first time.
