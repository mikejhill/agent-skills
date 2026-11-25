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

A preamble listing the files goes before your prompt. Claude with `--sandbox inherit`
gets no tool grants, so its own permission settings decide whether it can read files
outside `--cwd`.

## Output: generated images and `--out DIR`

Every task has an outputs folder: `--out DIR` (created if missing), or else
`<state home>/jobs/<job>/artifacts/`. When the job ends, `wait` and `result` list the
files under `artifacts:` (also in `--json`).

- **Codex images.** Codex's image-generation tool saves to
  `$CODEX_HOME/generated_images/<session>/` (default `~/.codex`). That happens outside
  the sandbox, so it works in read-only tasks. After the run the skill copies the
  session's new images into the outputs folder and leaves the originals. Images from
  earlier turns of a resumed session are not copied again. Ask for the image in plain
  words; Codex picks the tool. It needs a ChatGPT plan with image generation and the
  `image_generation` feature on (`codex features list`).
- **Other files.** With `--out`, the prompt tells the agent to save deliverables there
  and list them. Write access is limited to that folder where the target allows:
  - Claude Code, read-only task: `--add-dir DIR` plus an `Edit(//DIR/**)` rule. Other
    edits stay refused.
  - Codex with `--write`: the folder is added as a writable root next to `--cwd`.
  - Codex read-only: its sandbox can't grant one folder, so it can't write files. It is
    told that generated images are collected anyway. For other files, use `--write`
    with `--cwd` set to a scratch folder or a worktree.

Claude Code has no image generation of its own; it can still write files such as SVG,
HTML, or charts made with scripts it may run.

## Using the results

Open or view the files before you describe them to the user, and verify them as you
would any other output. Move or copy them where the user wants; the job's artifacts
folder is pruned with the job record (`cleanup --prune-days`, 7 days by default).
