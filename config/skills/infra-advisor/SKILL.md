---
name: infra-advisor
description: Use when the user describes a goal at the CERN/HEP infrastructure level and wants to know WHICH services to stitch (e.g. "I want distributed analysis on Open Data and to train an ML model"). Returns a 2–4-service stack with steps and pointers to the matching execution skill (`rucio`, `reana-workflows`, `physlite-basics`, …). Bundles a service catalogue (`reference/catalog.yaml`), pre-cooked recipes (`reference/recipes.md`), and digests on GPU access, SWAN+HTCondor scale-out, and columnar frameworks. Does NOT cover physics methodology, single-tool command-level help, or running specific code (use the dedicated skill named by the recommendation). Disambiguator phrase: CERN service stack composer.
data_scope: both
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

Read lazily. All one level deep from this SKILL.md.

- **`reference/catalog.yaml`** — structured service catalogue. One
  record per tool (purpose, audience, auth, entry URL, when-to-use,
  when-to-avoid, integrations, matching skill). Grep or read it.
- **`reference/recipes.md`** — pre-cooked stacks for common compound
  goals (public exploration, distributed analysis, reproducibility,
  ML training + serving, non-public datasets).
- **`reference/cern-gpus.md`** — distilled from
  https://clouddocs.web.cern.ch/gpu_overview.html. Read when the goal
  needs a GPU (training, vGPU, CUDA debugging). Routes between
  lxplus-gpu, SWAN (T4), HTCondor GPU, ml.cern.ch, OpenStack g*.
- **`reference/swan-htcondor.md`** — distilled from
  https://swan.docs.cern.ch/condor/intro/. Read when the user wants
  to develop in a SWAN notebook and scale out to the CERN HTCondor
  pool from the same session (interactive-plus-batch).
- **`reference/columnar-frameworks.md`** — uproot/awkward vs coffea
  vs (distributed) RDataFrame. Read when the user asks "which
  framework" or when a recipe needs to name one.

Pick the right file by intent: `recipes.md` when the user's goal
matches a named compound recipe; `catalog.yaml` when composing bespoke;
the three digest files when the topic (GPUs, SWAN scale-out,
columnar frameworks) is the centre of the question.

### Drift policy

The three digest files pin their **canonical upstream URL** at the
top, plus the date they were last refreshed. If you suspect drift
(user reports a command that doesn't work, or the digest is older
than ~6 months), WebFetch the canonical URL and compare before
answering from the digest. Do not bulk-re-fetch — only when you have
a concrete reason to suspect the note is stale.

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
| Scalable Python analysis over Open Data           | CERN AF (SWAN + HTCondor / lxplus / ml.cern.ch / REANA) or coffea-casa |
| ROOT/C++ shop scaling the same code local → batch | (distributed) RDataFrame on SWAN + HTCondor |
| Dev-in-notebook, run-in-batch                     | SWAN + HTCondor (Dask-HTCondor) → move_to_batch |
| Declarative, reproducible pipeline                | REANA + GitLab + container digest |
| Paper reproducibility + DOI                       | REANA + CVMFS + Zenodo |
| Non-public dataset discovery / transfer           | Rucio |
| Grid submission, ATLAS member                     | PanDA (on top of Rucio) |
| Large batch on CERN resources                     | HTCondor @ CERN |
| GPU sanity check / CUDA debug (interactive)       | lxplus-gpu (SSH) |
| ML training in a notebook (small/medium model)    | SWAN T4 GPU |
| ML training + inference endpoint                  | ml.cern.ch (Kubeflow) |
| A100 / custom CUDA stack, multi-week lease        | OpenStack g4.* flavor (ticket) |
| "Quick and cheap" answer, no CERN account         | Colab + atlas-opendata skill |

For the framework dimension ("which columnar library"), consult
`reference/columnar-frameworks.md` — it picks between uproot/awkward,
coffea, and (distributed) RDataFrame.

### On "the Analysis Facility"

When a user says *"the analysis facility"* at CERN, they usually mean
the **integrated CERN stack** (lxplus + SWAN + HTCondor batch + REANA
+ ml.cern.ch + Rucio + EOS + CVMFS) presented as one facility — not
any single product. The `cern-af` entry in `catalog.yaml` captures
this umbrella.

**coffea-casa** is a separate, external analysis facility (Dask on
Kubernetes tuned for coffea). It's one *instance* of the AF idea, not
THE AF. Recommend the CERN AF as the default for CERN users;
recommend coffea-casa when the user is already in the coffea
ecosystem and wants zero setup.

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
