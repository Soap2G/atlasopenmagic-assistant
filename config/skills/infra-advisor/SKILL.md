---
name: infra-advisor
description: Use this skill when the user describes a workflow or analysis goal at the infrastructure level and wants to know which CERN/HEP services and tools to stitch together (e.g. "I want to run distributed analysis on Open Data and train an ML model"). Produces a concrete stack recommendation — services, steps, links — not physics advice. Load when the user asks "how do I run…", "which tools for…", "where should I do X", or composes goals across data access + compute + ML + reproducibility. Do NOT load for pure physics methodology, specific code help, or single-tool questions (use the dedicated skill for that tool instead).
---

## Scope

Use this skill when the user is **orienting**, not executing. Signals:

- They describe a goal in English ("I want to …") rather than asking
  for a command.
- The goal spans multiple infra concerns: data access **and** compute
  **and** ML/reproducibility.
- They don't yet know what to pick between lxplus, SWAN, Binder, REANA,
  coffea-casa, ml.cern.ch, etc.

Don't use this skill when:
- The user already picked a tool and needs command-level help → use
  the dedicated skill (`rucio`, `reana`, `reana-workflows`,
  `atlas-opendata`, `cern-opendata`, `physlite-basics`, …).
- The question is physics methodology (how to measure σ·BR, which
  background to simulate) → use `sm-analyses` / `atlas-notebooks`.
- The user wants a single fact about one service (URL, auth type) →
  read `reference/catalog.yaml` directly, no advisory needed.

## Reference files

- **`reference/catalog.yaml`** — structured service catalogue. One
  record per tool (purpose, audience, auth, entry URL, when-to-use,
  when-to-avoid, integrations, matching skill). Grep or read it.
- **`reference/recipes.md`** — pre-cooked stacks for common compound
  goals (public exploration, distributed analysis, reproducibility,
  ML training + serving, non-public datasets).

Read both lazily — `recipes.md` first when the user's goal matches one
of the named recipes; `catalog.yaml` when composing a bespoke stack or
looking up a single service's details.

## Intake: five questions to triangulate

Before recommending, confirm these five axes. Ask any that aren't
obvious from the user's message — skip the ones already answered.

1. **Data source** — ATLAS Open Data release? CERN Open Data record
   (CMS/LHCb/ALICE)? Non-public experiment data? User's own files?
2. **Audience / auth tier** — Public user (no CERN account)? CERN
   account (lxplus/SWAN/GitLab)? ATLAS/CMS member (grid, Rucio)?
3. **Scale** — Laptop-minutes? A few hours on one node? Hundreds of
   core-hours distributed? GPU for ML?
4. **Reproducibility bar** — Throw-away exploration? Paper-grade
   pinned pipeline (DOI, container digests, declared outputs)?
   Teaching material someone else will re-run?
5. **Output shape** — Plots/notebook? Skimmed ntuples back to the
   user? A trained model + inference endpoint? A workflow that ships
   alongside a paper?

If the user gave you enough to answer three of five, proceed. Ask
one clarifying question rather than five — keep friction low.

## Recommendation format

Produce a short, scannable block with four parts:

1. **TL;DR stack** — one line naming the 2–4 services to stitch.
2. **Why this stack** — 2–3 bullets tying each service to a specific
   intake answer ("public data → no Rucio needed", "ML training → GPU
   → ml.cern.ch Kubeflow, not SWAN").
3. **Steps** — numbered, concrete, each step names the tool and the
   exit artifact. Link the matching skill when Claude has one
   (`rucio`, `reana-workflows`, etc.) so the user can drill down.
4. **Caveats** — auth pre-reqs, quotas, obvious failure modes. Keep
   to 2–3 bullets.

End with a concrete call to action: one CLI command or one URL the
user should open next.

## Decision cheatsheet

Use this to prune the catalogue fast. Full details in
`reference/recipes.md`.

| Goal                                              | Default stack |
|---------------------------------------------------|---------------|
| Classroom / first look at HEP data                | ATLAS Open Data + Binder |
| Interactive notebook, CERN user                   | SWAN + EOS + CVMFS |
| Scripted local analysis, any user                 | `uproot`/`coffea` + Docker image |
| Scalable Python analysis over Open Data           | coffea-casa (AF) + ATLAS/CMS Open Data |
| Declarative, reproducible pipeline                | REANA + GitLab + container digest |
| Paper reproducibility + DOI                       | REANA + CVMFS + Zenodo |
| Non-public dataset discovery / transfer           | Rucio |
| Grid submission, ATLAS member                     | PanDA (on top of Rucio) |
| Large batch on CERN resources                     | HTCondor @ CERN |
| ML training on GPU + inference endpoint           | Rucio → SWAN/ml.cern.ch → Kubeflow serve |
| "Quick and cheap" answer, no CERN account         | Colab + atlas-opendata skill |

If the goal composes two rows (e.g. "distributed analysis **and** ML"),
compose the stacks — that's the whole point of this skill. Example in
`reference/recipes.md#distributed-analysis-plus-ml`.

## Workflow

1. **Listen** for intake answers in the user's first message. Fill in
   gaps with one focused question if needed.
2. **Match a recipe** in `reference/recipes.md` if the goal is close
   to a named one; otherwise **compose from `catalog.yaml`**.
3. **Produce the recommendation** in the four-part format above.
4. **Hand off** to the tool-specific skill for execution. E.g. if the
   stack says "declare with REANA", load `reana-workflows` next.

## Pitfalls

- **Don't overload the user.** Three tools is often the right
  answer; five is never. If the stack has more than four services,
  merge steps or split into phases.
- **Respect the audience tier.** Don't recommend Rucio or lxplus to
  a classroom user; don't recommend Binder for a paper-grade pipeline.
- **Check integrations.** `catalog.yaml` lists `integrates_with:` per
  service — if you propose two services that don't, flag the seam
  (e.g. "you'll need to `rucio download` locally before `reana-client
  upload`").
- **Links can rot.** Give the canonical top-level URL
  (`https://reana.cern.ch`, `https://opendata.atlas.cern`) plus the
  matching skill name — let the dedicated skill handle command-level
  detail.
- **Don't do physics.** This skill is infra-only. Push physics
  methodology questions to `sm-analyses` or a reference.

## Verification

A successful use of this skill ends with the user holding:
- a named stack (2–4 services),
- the first concrete action (one URL or one CLI command), and
- the name of the next skill to load (`rucio`, `reana-workflows`,
  `atlas-opendata`, …) when they're ready to execute.

If the user walks away still unsure which service to start with, the
recommendation was too broad — compress.
