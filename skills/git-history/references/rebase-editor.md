# Non-interactive rebase todo editing

Agents cannot use an interactive editor. Point `GIT_SEQUENCE_EDITOR` at a script that inserts `break` at the top of the todo list. The rebase then stops before applying anything, and you edit the todo file as a normal file.

## Bash

```bash
editor="$(mktemp)"
cat > "$editor" <<'SH'
#!/bin/sh
{ printf 'break\n'; cat "$1"; } > "$1.new" && mv "$1.new" "$1"
SH
chmod +x "$editor"
GIT_SEQUENCE_EDITOR="$editor" git rebase -i --autostash <target-hash>~1
```

## PowerShell

```powershell
$Editor = Join-Path ([IO.Path]::GetTempPath()) "git-rebase-editor-$(Get-Date -Format yyyyMMdd-HHmmss).sh"
Set-Content -Path $Editor -NoNewline -Value "#!/bin/sh`n{ printf 'break\n'; cat `"`$1`"; } > `"`$1.new`" && mv `"`$1.new`" `"`$1`"`n"
$env:GIT_SEQUENCE_EDITOR = $Editor.Replace('\', '/').Replace(' ', '\ ')
git rebase -i --autostash <target-hash>~1
Remove-Item Env:GIT_SEQUENCE_EDITOR
```

Git for Windows runs the editor through its bundled `sh`, so the script stays POSIX sh on every OS.

## Edit the todo

- Path: `git rev-parse --git-path rebase-merge/git-rebase-todo`.
- The `break` has already run, so the file holds the remaining `pick <hash> <subject>` lines, oldest first.
- Change words, reorder, or delete lines, then `git rebase --continue`.

| Action | Effect |
| --- | --- |
| `pick` | Keep as is |
| `reword` | Keep, and open `GIT_EDITOR` for the message. Agents use `edit` plus `git commit --amend -m` instead. |
| `edit` | Keep, stop to amend content or split |
| `squash` | Meld into the previous commit and combine messages |
| `fixup` | Meld into the previous commit and drop this message |
| `drop` | Remove the commit |

For `squash`, Git opens `GIT_EDITOR` for the combined message. Set `GIT_EDITOR=true` to accept it as is, or use `fixup` and reword the target separately.
