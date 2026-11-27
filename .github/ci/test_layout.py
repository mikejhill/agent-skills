"""Checks for the harness-folder convention (README: Harness-specific items).

Items for one harness live under harnesses/<harness>/<kind>/. Each harness
folder is a separate SkillSinc source routed to that harness alone, so:

- <harness> must be a SkillSinc profile that a route can target;
- only kind folders SkillSinc reads may appear inside it;
- an item name may not also exist at the root, or one destination would get
  two different items with the same name;
- a harness folder may not be empty, because a configured source whose
  folder is missing fails.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HARNESSES = REPO / "harnesses"
PROFILES = {"claude", "codex", "copilot", "vscode"}
KINDS = {"skills", "instructions", "agents", "prompts", "mcp", "resources", "hooks"}
SUFFIXES = (".instructions.md", ".agent.md", ".prompt.md", ".intent.md", ".json", ".md")


def item_name(path: Path) -> str:
    if path.is_dir():
        return path.name
    for suffix in SUFFIXES:
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)]
    return path.stem


def items(kind_dir: Path) -> set[str]:
    if not kind_dir.is_dir():
        return set()
    return {
        item_name(p)
        for p in kind_dir.iterdir()
        if not p.name.startswith(".") and not p.name.endswith(".intent.md")
    }


def harness_dirs() -> list[Path]:
    if not HARNESSES.is_dir():
        return []
    return sorted(p for p in HARNESSES.iterdir() if not p.name.startswith("."))


def test_harness_folders_are_profiles() -> None:
    for d in harness_dirs():
        assert d.is_dir(), f"{d.relative_to(REPO)}: expected a folder"
        assert d.name in PROFILES, f"harnesses/{d.name}: not one of {sorted(PROFILES)}"


def test_harness_folders_hold_kind_folders_only() -> None:
    for d in harness_dirs():
        children = [p for p in d.iterdir() if not p.name.startswith(".")]
        assert children, f"harnesses/{d.name} is empty; remove it and its SkillSinc source"
        for child in children:
            assert child.is_dir() and child.name in KINDS, (
                f"{child.relative_to(REPO).as_posix()}: only {sorted(KINDS)} folders belong here"
            )
            assert items(child), f"{child.relative_to(REPO).as_posix()} is empty"


def test_harness_items_do_not_shadow_root_items() -> None:
    for d in harness_dirs():
        for kind in KINDS:
            clash = items(d / kind) & items(REPO / kind)
            assert not clash, f"harnesses/{d.name}/{kind}: also at the root: {sorted(clash)}"
