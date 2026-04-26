#!/usr/bin/env python3
"""Skill-router eval harness.

Implements Principle 8 of the Skill Library Design Guide — Cern Assistant.

Loads every skill `description` (under `config/skills/**/SKILL.md`) and
every agent `description` (under `config/agents/*.md`), then asks a
configured model to act as the router on each prompt in `cases.yaml`.
Reports per-skill precision and recall; exits non-zero if any case fails.

Usage:

    # From the repo root:
    export ANTHROPIC_API_KEY=...
    python config/evals/run.py

    # Override the model (any Anthropic model id works):
    EVAL_MODEL=claude-sonnet-4-6 python config/evals/run.py

Dependencies: `pyyaml` and `httpx` (both pip-installable).
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "config" / "skills"
AGENTS_DIR = ROOT / "config" / "agents"
CASES_FILE = ROOT / "config" / "evals" / "cases.yaml"

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("EVAL_MODEL", "claude-haiku-4-5")


def load_frontmatter(path: Path) -> dict:
    """Parse the leading YAML frontmatter of a markdown file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def collect_skills() -> list[dict]:
    """Walk the skills + agents tree and return name/description records."""
    out: list[dict] = []
    for path in SKILLS_DIR.rglob("SKILL.md"):
        fm = load_frontmatter(path)
        name = fm.get("name") or path.parent.name
        if desc := fm.get("description"):
            out.append({"name": name, "kind": "skill", "description": desc})
    for path in AGENTS_DIR.glob("*.md"):
        fm = load_frontmatter(path)
        if desc := fm.get("description"):
            out.append({"name": path.stem, "kind": "agent", "description": desc})
    return sorted(out, key=lambda s: (s["kind"], s["name"]))


def build_router_prompt(skills: list[dict], user_prompt: str) -> str:
    lines = [
        "You are the skill router for a CERN / HEP assistant.",
        "Given the user query, output ONLY the name of the single best",
        "matching skill or agent, or the literal token NONE if no entry",
        "applies. Do not explain — just emit the name on its own line.",
        "",
        "Available entries:",
        "",
    ]
    for s in skills:
        lines.append(f"- {s['name']} ({s['kind']}): {s['description']}")
    lines += ["", f"User query: {user_prompt}", "", "Answer:"]
    return "\n".join(lines)


def call_model(prompt: str, model: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set; aborting.")
    resp = httpx.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 32,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()


def parse_choice(reply: str, valid: set[str]) -> str:
    """Pull the first token from `reply` that matches a valid name or NONE."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]*", reply)
    for tok in tokens:
        if tok == "NONE":
            return "NONE"
        if tok in valid:
            return tok
    for name in valid:
        if name in reply:
            return name
    return "NONE"


def run() -> int:
    skills = collect_skills()
    valid_names = {s["name"] for s in skills}
    cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))

    print(f"Eval harness — model: {DEFAULT_MODEL}")
    print(f"Loaded {len(skills)} entries: " + ", ".join(s["name"] for s in skills))
    print()

    pred_for_truth: dict[str, list[str]] = defaultdict(list)
    truth_for_pred: dict[str, list[str]] = defaultdict(list)
    fails: list[tuple[str, str, str]] = []

    for case in cases.get("should_match", []):
        truth = case.get("skill") or case.get("agent")
        if truth not in valid_names:
            sys.exit(f"cases.yaml references unknown entry: {truth!r}")
        for prompt in case["prompts"]:
            pred = parse_choice(call_model(build_router_prompt(skills, prompt), DEFAULT_MODEL), valid_names)
            pred_for_truth[truth].append(pred)
            truth_for_pred[pred].append(truth)
            mark = "OK " if pred == truth else "FAIL"
            print(f"  [{mark}] expect {truth:24s}  got {pred:24s}  prompt={prompt!r}")
            if pred != truth:
                fails.append((truth, prompt, pred))

    print("\nshould_not_match:")
    for prompt in cases.get("should_not_match", []):
        pred = parse_choice(call_model(build_router_prompt(skills, prompt), DEFAULT_MODEL), valid_names)
        ok = pred == "NONE"
        mark = "OK " if ok else "FAIL"
        print(f"  [{mark}] expect NONE                      got {pred:24s}  prompt={prompt!r}")
        if not ok:
            fails.append(("NONE", prompt, pred))

    print("\nPer-skill recall:")
    for truth, preds in sorted(pred_for_truth.items()):
        hits = sum(p == truth for p in preds)
        print(f"  {truth:24s}  {hits}/{len(preds)}")

    print("\nPer-skill precision:")
    for pred, truths in sorted(truth_for_pred.items()):
        if pred == "NONE":
            continue
        hits = sum(t == pred for t in truths)
        print(f"  {pred:24s}  {hits}/{len(truths)}")

    print(f"\n{len(fails)} failure(s).")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
