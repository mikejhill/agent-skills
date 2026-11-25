# Files and images

`task` can hand the other agent files and bring back the files it makes.

```text
xh.py task -t codex --attach mock.png --attach notes.md "Redesign this screen; explain the changes."
xh.py task -t codex "Generate a 1024x1024 app icon: a paper plane on a teal background."
xh.py task -t claude --out ./out --attach data.csv "Plot weekly totals as an SVG."
```

## Input: `--attach FILE`

Repeatable. Paths are checked first (Codex silently drops a missing image) and passed
as absolute paths.

| Target | Images (`.png .jpg .jpeg .webp .gif`) | Other files |
|---|---|---|
| Codex | Image input on the prompt (`-i`), also on `--resume` | Listed in the prompt; Codex opens them with its own tools |
| Claude Code | Listed in the prompt; its Read tool views images | Listed in the prompt; Read handles text and PDF |

A preamble listing the files goes before your prompt. Codex splits `-i` values on
commas, so an image whose path has a comma is listed instead of attached. Claude with
`--sandbox inherit` gets no tool grants, so its own permission settings decide whether
it can read files outside `--cwd`. Codex needs `--cwd` inside a Git repository, as for
any task.

## Output: generated images and `--out DIR`

Every task has an outputs folder: `--out DIR` (created if missing), or else
`<state home>/jobs/<job>/artifacts/`. When the job ends, `wait` and `result` list the
files under `artifacts:` (also in `--json`): copied images, plus files that are new or
changed in the folder since the job started. A failed copy shows as `artifact error:`
and fails the job.

- **Codex images.** Codex's image-generation tool saves to
  `$CODEX_HOME/generated_images/<session>/` (default `~/.codex`). Codex itself writes
  there, outside the model's sandbox, so it works in read-only tasks. After the run the
  skill copies the session's new images into the outputs folder under unused names and
  leaves the originals. A resumed session's earlier images are not copied again. Ask
  for the image in plain words; Codex picks the tool. It needs a ChatGPT plan with image
  generation and the `image_generation` feature on (`codex features list`). An answer
  with images and no text counts as success.
- **Other files** need `--write`. With `--write --out DIR`, the prompt tells the agent to
  save deliverables in `DIR` and list them, and `DIR` becomes writable next to `--cwd`
  (Claude Code `--add-dir`; Codex `--add-dir`, or on `--resume` a
  `sandbox_workspace_write.writable_roots` override for that run). Read-only tasks
  stay read-only: the prompt says the run can't write files. To keep the repository
  untouched, point `--cwd` at a scratch folder or a worktree.

Claude Code has no image generation of its own; it can still write files such as SVG,
HTML, or charts made with scripts it may run.

On Windows, Codex's `workspace-write` sandbox can fail to start commands ("no writable
root capability SIDs"). Codex then asks for escalation, and whether the write happens
depends on the user's Codex approval settings. Generated images are unaffected.

## Using the results

Open or view the files before you describe them to the user, and verify them as you
would any other output. Move or copy them where the user wants; the job's artifacts
folder is pruned with the job record (`cleanup --prune-days`, 7 days by default).
