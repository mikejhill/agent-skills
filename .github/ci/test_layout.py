"""Checks for the harness-folder convention (README: Harness-specific items).

Items for one harness live under harnesses/<harness>/<kind>/. Each harness
folder is a separate SkillSinc source routed to that harness alone, so:

- <harness> must be a SkillSinc profile that a route can target;
- only kind folders that profile writes may appear inside it
  (`skillsinc harnesses`), or the route silently delivers nothing;
- each kind folder holds only entries SkillSinc reads as items;
- an item name may not also exist at the root, or one destination would get
  two different items with the same name;
- a harness folder may not be empty, because a configured source whose
  folder is missing fails.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HARNESSES = REPO / "harnesses"
# Kinds each SkillSinc profile writes (`skillsinc harnesses`, SkillSinc 0.10).
PROFILE_KINDS = {
    "claude": {"skills", "instructions", "agents", "prompts", "mcp", "resources", "hooks"},
    "codex": {"instructions", "agents", "mcp"},
    "copilot": {"skills", "instructions", "agents", "mcp", "resources", "hooks"},
    "vscode": {"instructions", "agents", "prompts", "mcp"},
}
# File suffix SkillSinc reads per kind; skills are folders with a SKILL.md.
SUFFIX = {
    "instructions": ".instructions.md",
    "agents": ".agent.md",
    "prompts": ".prompt.md",
    "mcp": ".json",
    "resources": ".md",
    "hooks": ".json",
}
KINDS = {"skills", *SUFFIX}


def item_name(kind: str, path: Path) -> str | None:
    """The item name SkillSinc gives this entry, or None if it is not an item."""
    if path.name.startswith(".") or path.name.endswith(".intent.md") or path.name == "INTENT.md":
        return None
    if kind == "skills":
        return path.name if path.is_dir() and (path / "SKILL.md").is_file() else None
    suffix = SUFFIX[kind]
    if path.is_file() and path.name.endswith(suffix) and len(path.name) > len(suffix):
        return path.name[: -len(suffix)]
    return None


def stray(kind_dir: Path) -> list[str]:
    """Entries in a kind folder that are neither items nor intent sidecars."""
    out = []
    for p in kind_dir.iterdir():
        if p.name.startswith("."):
            continue
        if item_name(kind_dir.name, p) is None and not p.name.endswith(".intent.md"):
            out.append(p.relative_to(REPO).as_posix())
    return out


def items(kind_dir: Path) -> set[str]:
    if not kind_dir.is_dir():
        return set()
    names = (item_name(kind_dir.name, p) for p in kind_dir.iterdir())
    return {n for n in names if n}


def harness_dirs() -> list[Path]:
    if not HARNESSES.is_dir():
        return []
    return sorted(p for p in HARNESSES.iterdir() if not p.name.startswith("."))


def test_harness_folders_are_profiles() -> None:
    for d in harness_dirs():
        assert d.is_dir(), f"{d.relative_to(REPO)}: expected a folder"
        assert d.name in PROFILE_KINDS, f"harnesses/{d.name}: not one of {sorted(PROFILE_KINDS)}"


def test_harness_folders_hold_supported_kinds_only() -> None:
    for d in harness_dirs():
        children = [p for p in d.iterdir() if not p.name.startswith(".")]
        assert children, f"harnesses/{d.name} is empty; remove it and its SkillSinc source"
        allowed = PROFILE_KINDS.get(d.name, set())
        for child in children:
            rel = child.relative_to(REPO).as_posix()
            assert child.is_dir() and child.name in KINDS, f"{rel}: only kind folders {sorted(KINDS)} belong here"
            assert child.name in allowed, f"{rel}: SkillSinc's {d.name} profile does not write {child.name}"
            assert items(child), f"{rel} holds no item SkillSinc reads"
            assert not stray(child), f"{rel}: not items SkillSinc reads: {stray(child)}"


def test_harness_items_do_not_shadow_root_items() -> None:
    for d in harness_dirs():
        for kind in KINDS:
            clash = items(d / kind) & items(REPO / kind)
            assert not clash, f"harnesses/{d.name}/{kind}: also at the root: {sorted(clash)}"


def test_item_name_classification(tmp_path: Path) -> None:
    (tmp_path / "review.txt").write_text("x", encoding="utf-8")
    (tmp_path / "review.instructions.md").write_text("x", encoding="utf-8")
    (tmp_path / "review.intent.md").write_text("x", encoding="utf-8")
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "SKILL.md").write_text("x", encoding="utf-8")
    (tmp_path / "empty").mkdir()
    assert item_name("instructions", tmp_path / "review.txt") is None
    assert item_name("instructions", tmp_path / "review.instructions.md") == "review"
    assert item_name("instructions", tmp_path / "review.intent.md") is None
    assert item_name("prompts", tmp_path / "review.instructions.md") is None
    assert item_name("skills", tmp_path / "s") == "s"
    assert item_name("skills", tmp_path / "empty") is None
