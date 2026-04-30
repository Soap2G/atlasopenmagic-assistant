#!/usr/bin/env python3
"""Structural validator for the skill / agent library.

Pure-Python, no API calls, no network. Safe to run in CI on every PR
(including PRs from forks). Fails fast with a non-zero exit code if any
of the following invariants are violated:

1. Every `config/skills/**/SKILL.md` and `config/agents/*.md` has YAML
   frontmatter with a non-empty `description`.
2. Skills have a `name:` field; agents inherit their name from the
   filename stem.
3. All names across skills + agents are unique (router collisions are
   silent failures otherwise).
4. Every `should_match` entry in `config/evals/cases.yaml` references
   a name that exists in the library.
5. Every entry has at least one prompt; `should_not_match` is a flat
   list of strings.

Run from the repo root:

    python config/evals/lint.py

NOTE on parsing: top-level `name:` and `description:` are extracted
with a forgiving line-oriented regex rather than `yaml.safe_load`,
because skill descriptions intentionally contain `": "` (e.g.
"Disambiguator phrase: …") which is illegal in unquoted YAML scalars.
Quoting every description is the alternative; we chose tolerant
parsing instead so that authors don't have to escape natural language.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "config" / "skills"
AGENTS_DIR = ROOT / "config" / "agents"
CASES_FILE = ROOT / "config" / "evals" / "cases.yaml"


def extract_frontmatter(text: str) -> str | None:
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, flags=re.DOTALL)
    return m.group(1) if m else None


def extract_field(fm: str, key: str) -> str | None:
    """Pull a top-level `key: value` line, value taken raw to end of line.

    Tolerates embedded `: ` inside the value (e.g. "Disambiguator
    phrase: ..."), which strict YAML rejects.
    """
    pat = rf"^{re.escape(key)}:\s*(.+?)\s*$"
    m = re.search(pat, fm, flags=re.MULTILINE)
    return m.group(1).strip() if m else None


def main() -> int:
    errors: list[str] = []
    names: dict[str, Path] = {}

    skill_paths = sorted(SKILLS_DIR.rglob("SKILL.md"))
    if not skill_paths:
        errors.append(f"no SKILL.md files found under {SKILLS_DIR}")

    for path in skill_paths:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: missing frontmatter (--- ... ---)")
            continue
        name = extract_field(fm, "name")
        desc = extract_field(fm, "description")
        if not name:
            errors.append(f"{rel}: frontmatter missing `name:`")
            continue
        if not desc:
            errors.append(f"{rel}: frontmatter missing `description:`")
        if name in names:
            errors.append(
                f"{rel}: duplicate name {name!r} (also in {names[name].relative_to(ROOT)})"
            )
        else:
            names[name] = path

    for path in sorted(AGENTS_DIR.glob("*.md")):
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: missing frontmatter (--- ... ---)")
            continue
        if not extract_field(fm, "description"):
            errors.append(f"{rel}: frontmatter missing `description:`")
        name = path.stem
        if name in names:
            errors.append(
                f"{rel}: agent name {name!r} collides with skill at "
                f"{names[name].relative_to(ROOT)}"
            )
        else:
            names[name] = path

    if CASES_FILE.exists():
        cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8")) or {}
        for case in cases.get("should_match", []):
            truth = case.get("skill") or case.get("agent")
            if not truth:
                errors.append("cases.yaml: should_match entry has no skill/agent key")
                continue
            if truth not in names:
                errors.append(
                    f"cases.yaml: should_match references unknown name {truth!r}"
                )
            prompts = case.get("prompts") or []
            if not prompts:
                errors.append(f"cases.yaml: {truth!r} has no prompts")

        snm = cases.get("should_not_match")
        if snm is not None and not isinstance(snm, list):
            errors.append("cases.yaml: should_not_match must be a list of strings")
    else:
        errors.append(f"missing {CASES_FILE.relative_to(ROOT)}")

    print(f"Validated {len(names)} entries: " + ", ".join(sorted(names)))
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nAll structural checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
