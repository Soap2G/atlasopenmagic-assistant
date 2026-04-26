# Skill-router eval harness

> Implements **Principle 8** of the *Skill Library Design Guide — CERN
> Assistant*. Manual review will not catch the confusability cliff;
> only a frozen prompt-set regression suite will.

## What it measures

Top-1 selection accuracy of the skill router. For each prompt in
`cases.yaml` the harness:

1. Loads every `description` from `config/skills/**/SKILL.md` and
   `config/agents/*.md`.
2. Presents them to a configured model in a routing prompt.
3. Compares the model's choice against the expected ground-truth
   skill / agent name (or `NONE` for the should-not-match set).

The output is per-skill **precision** and **recall**, plus a list of
failures with the prompt and the wrong choice the model made.

## Running it

```bash
# From the repo root:
export ANTHROPIC_API_KEY=sk-ant-...
pip install pyyaml httpx        # if not already installed
python config/evals/run.py
```

Override the model with `EVAL_MODEL` (any Anthropic model id):

```bash
EVAL_MODEL=claude-sonnet-4-6 python config/evals/run.py
```

Exit code is `0` if all cases pass, `1` if any fail. Wire it into
`pre-commit` or CI to catch regressions on every description change.

## When you add or rename a skill

Per **Principle 7 step 7** of the design guide, every new skill ships
with **3–5 prompts that should select it** plus 2 that should not.
Add them to `cases.yaml` under `should_match` (or `should_not_match`)
in the same PR that adds the skill. Then run the harness — if it
regresses on a *pre-existing* skill, the new description overlaps too
much. Revise before merging.

## When the cliff arrives locally

Watch for this pattern: adding skill **N** in category **X** breaks
recall on a *different* skill **M** that lives in the same category.
That is the confusability cliff arriving for category **X**. The fix
is description surgery on whichever of N or M is broader, **not**
adding more skills or hierarchy.

## File layout

```
config/evals/
├── cases.yaml      # ground truth — prompts × expected skill name
├── run.py          # the harness
└── README.md       # this file
```

## Limits of this harness

- **Single-step routing only.** It tests "given prompt, pick one
  skill". Multi-step planning ("find a dataset, stage it, fit, plot")
  is out of scope — that needs a planning agent or composite
  workflow skills, not a router-accuracy test.
- **Model is a proxy for opencode's router.** The harness uses a
  generic model in router-prompt mode rather than driving opencode
  directly, so absolute numbers may differ from what opencode does
  internally. Trends and regressions still track.
- **Doesn't test MCP-tool descriptions.** Per Principle 6 those
  count toward the same router; extending the harness to query an
  opencode-running session is a follow-up.
