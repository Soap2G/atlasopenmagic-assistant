# Infra recipes

Pre-composed stacks for common compound goals. Each recipe names:
the goal, the stack, the steps in order, the caveats, and the next
skill to load for execution.

When the user's goal matches a recipe, start from it. When it doesn't,
compose from `catalog.yaml` using the intake questions in `SKILL.md`.

## Contents
- classroom-exploration — public, no account, teaching
- interactive-cern-user — notebook at CERN
- scalable-open-data-analysis — columnar scale-out
- notebook-to-batch — SWAN + HTCondor, interactive-plus-batch
- reproducible-paper-pipeline — declarative + DOI
- non-public-datasets — experiment-member grid work
- distributed-analysis-plus-ml — user's example: Open Data + distributed analysis + ML

---

## classroom-exploration

**Goal** — "I'm teaching / self-learning, no CERN account, want to
play with real LHC data."

**Stack** — ATLAS Open Data portal + Binder (or Colab for GPU toys).

**Steps**
1. Browse `https://opendata.atlas.cern` for a tutorial matching the
   topic (Higgs, Z, top, …). Load the `atlas-notebooks` skill for
   routing.
2. Click the Binder badge on the tutorial repo — or open the notebook
   in Colab — to get a ready-to-run environment.
3. Inside the notebook, use the `atlas_get_urls` MCP tool to grab
   public HTTPS / XRootD URIs; open them with `uproot.open`.

**Caveats**
- Binder sessions die after ~1 h of inactivity; save outputs locally.
- No persistent storage — copy results out before closing.

**Next skill** — `atlas-notebooks`, then `physlite-basics`.

---

## interactive-cern-user

**Goal** — "I have a CERN account and want a Jupyter with the ATLAS
stack pre-installed."

**Stack** — SWAN + CVMFS (+ EOS for data).

**Steps**
1. Log in to `https://swan.cern.ch` with CERN SSO.
2. Pick a software stack from the CVMFS menu (LCG / ATLAS /
   user-defined).
3. Mount your EOS project area from the session settings.
4. Open a notebook; `uproot`/`coffea`/`ROOT` are already on PATH.

**Caveats**
- SWAN sessions are time-bound; save notebooks to EOS, not to the
  container.
- For GPU work, SWAN is not the right choice — see
  `distributed-analysis-plus-ml`.

**Next skill** — `physlite-basics`.

---

## scalable-open-data-analysis

**Goal** — "I want to run a columnar analysis over the whole
Open Data 13 TeV release and not wait all day."

**Stack** — ATLAS Open Data + an analysis facility (the **CERN AF**
for CERN users, **coffea-casa** as an external alternative) +
(optional) REANA wrapper for reproducibility.

**Picking the facility**
- **CERN AF** (SWAN + HTCondor + EOS + CVMFS) — native on-site path
  for CERN users. Same session develops and scales.
- **coffea-casa** (https://coffea.casa) — pre-tuned Dask cluster,
  quickest path if the user is already a coffea user and doesn't want
  to configure anything.
- Both are valid "analysis facilities"; coffea-casa is one particular
  implementation, the CERN AF is an umbrella over the integrated CERN
  stack.

**Steps**
1. Use `atlas_get_urls` (atlasopenmagic MCP) to resolve the full file
   list per DSID.
2. Enter the facility:
   - CERN AF — open https://swan.cern.ch with the HTCondor pool
     enabled, platform AlmaLinux9.
   - coffea-casa — log in to https://coffea.casa (CERN SSO or token).
3. Write the analysis in the framework matching the ecosystem:
   coffea for Python columnar, distributed RDataFrame for ROOT/C++.
4. Scale out — `SwanHTCondorCluster` + Dask on the CERN AF, or the
   pre-provisioned Dask cluster on coffea-casa.
5. When the analysis stabilises, wrap it in a `reana.yaml` (serial or
   snakemake) so anyone can re-run it.

**Caveats**
- Quotas on both facilities are per-user; don't hoard a cluster
  overnight.
- Streaming TB over XRootD is faster than downloading, but only if
  your processor stays in the lazy-columnar idiom.

**Next skill** — `physlite-basics`, then `reana-workflows` when
pinning. See `columnar-frameworks.md` to pick between uproot+awkward,
coffea, and distributed RDataFrame.

---

## notebook-to-batch

**Goal** — "I want to develop my analysis interactively in a
notebook, then run the same code as a batch job — without rewriting
anything."

**Stack** — SWAN + Dask-HTCondor + (later) plain `condor_submit`.

**Steps**
1. Start a SWAN session (`https://swan.cern.ch`) with platform
   AlmaLinux9 and the HTCondor pool enabled in the session form.
2. In the notebook, create a `SwanHTCondorCluster`, `cluster.scale(N)`,
   and connect a `dask.distributed.Client`. The Dask JupyterLab
   extension gives you a GUI for the same. Upstream docs:
   https://swan.docs.cern.ch/condor/intro/.
3. Use any Dask-aware framework — distributed RDataFrame, coffea with
   the Dask executor, or `dask.dataframe`/`dask.array`.
4. Once the analysis stabilises, dump the driver to a `.py` file and
   run the same code from lxplus via `condor_submit`
   (`condor/move_to_batch/` in SWAN docs).
5. For paper-grade reproducibility, wrap the batch command in a
   `reana.yaml` serial step — `reana-workflows` skill.

**Caveats**
- Start with `cluster.scale(2-4)`, not hundreds — you share the farm.
- Version drift on `dask-lxplus` / `SwanHTCondorCluster` is real;
  check the upstream docs if imports break.
- CPU only. For GPU work see https://clouddocs.web.cern.ch/gpu_overview.html.

**Next skill** — none specific; this is an infra-only recipe.
`reana-workflows` when pinning the script for reproducibility.

---

## reproducible-paper-pipeline

**Goal** — "I'm publishing and need the analysis to run bit-identically
from a DOI for the next decade."

**Stack** — REANA + container digests + CVMFS + Zenodo.

**Steps**
1. Draft a `reana.yaml`; pin container images by digest
   (`image@sha256:…`), not by tag. Use `reana-workflows` skill.
2. Declare all inputs under `inputs.files` / `inputs.directories`,
   all produced artefacts under `outputs.files`.
3. `reana-client validate` → `create` → `upload` → `start` → confirm
   `status == finished` → `download`.
4. Push the repo (with `reana.yaml`) to CERN GitLab.
5. Mint a Zenodo DOI on a tagged release. Reference the DOI from the
   paper.

**Caveats**
- Moving tags (`:latest`) kill long-term reproducibility. Warn if the
  user pushes an unpinned image.
- CVMFS paths drift too; pin to a versioned path
  (`/cvmfs/sw.escape.eu/rucio/38.3.0/`), not `latest`.

**Next skill** — `reana-workflows`.

---

## non-public-datasets

**Goal** — "I'm an ATLAS member and need to locate / run over
non-public samples."

**Stack** — Rucio + lxplus + (HTCondor for local batch, or PanDA for
the grid).

**Steps**
1. `ssh lxplus.cern.ch`; `setupATLAS && lsetup rucio`.
2. Set up auth: `voms-proxy-init -voms atlas` (or configure OIDC). The
   `rucio` skill covers the auth-type matrix.
3. Locate the dataset: `rucio did list '<scope>:<pattern>'` →
   `rucio did show <did>` → `rucio replica list dataset <did>`.
4. For local batch: write a `condor_submit` file that reads the
   dataset via `rucio download` or XRootD.
5. For grid-scale: submit via `prun` (PanDA); PanDA resolves Rucio
   inputs automatically.

**Caveats**
- VOMS proxies expire in 24 h — long grid jobs use long-lived proxies
  via `voms-proxy-init -valid 96:00`.
- PanDA is ATLAS-only; CMS uses CRAB, LHCb uses DIRAC.

**Next skill** — `rucio`.

---

## distributed-analysis-plus-ml

**Goal** (user example) — "I want to use the Open Data to run a
distributed analysis on both MC and data, and train an ML model on
the result."

**Stack** — ATLAS Open Data + (SWAN+HTCondor **or** coffea-casa **or**
REANA) + (SWAN T4 or ml.cern.ch for training).

**Framework choice** — see `columnar-frameworks.md`.
- Python/columnar shop → **coffea** on SWAN+HTCondor or coffea-casa.
- ROOT/C++ shop → **distributed RDataFrame** on SWAN+HTCondor (same
  code scales with a Dask client swap).

**Steps**
1. **Data access**: use `atlas_get_urls` to resolve per-DSID file
   lists. No Rucio needed — URIs are public
   (`root://eospublic.cern.ch/…`).
2. **Distributed analysis**: pick one:
   - **SWAN + HTCondor (Dask)** — develop in a notebook, scale to the
     CERN pool with a `SwanHTCondorCluster` client. See
     `swan-htcondor.md`. Best if the user wants one session that does
     both develop and scale.
   - **coffea-casa** — if the user is already a coffea user and wants
     the pre-tuned Dask cluster.
   - **REANA** (serial or snakemake) — if the analysis has stabilised
     and needs to be pinned and shareable.
3. **Feature export**: analysis writes training tensors (parquet /
   HDF5 / ROOT) into an EOS project area or a REANA workspace.
4. **ML training** — choose the GPU tier. See `cern-gpus.md`.
   - **SWAN T4** — small/medium models, want to stay in Jupyter.
   - **ml.cern.ch (Kubeflow)** — larger models, training + serving.
   - **OpenStack g4 (A100)** — multi-week lease, custom CUDA stack
     (requires a ticket to GPU Platform Consultancy).
   - **Colab** — non-CERN user; training only, no CERN-side serving.
5. **Serving**: on ml.cern.ch, wrap the trained model as a KFServing
   / Seldon endpoint; get a stable inference URL.
6. **Reproducibility tie-back** (optional): version the training code
   in CERN GitLab, mint a Zenodo DOI on tag, wrap the whole
   extract → train → export pipeline in REANA so a reviewer can
   replay it end-to-end.

**Caveats**
- ml.cern.ch is for CERN users; a public-only audience can swap it
  for Colab (GPU) for training, but serving won't be reachable from
  CERN infra.
- Keep the feature-extraction step deterministic (no random seeds)
  so training inputs are reproducible.
- GPU quota at CERN is scarce — size the training job to the GPU
  tier you can realistically hold. Lease scrutiny increases beyond
  ~4 months.

**Next skills** — `atlas-opendata` → (`reana-workflows` or
`physlite-basics` for coffea, or `columnar-frameworks.md` for
RDataFrame) → then outside-skill pointer to ml.cern.ch docs.

---

## Composition patterns

Two reminders when you stitch recipes together:

- **Data handoff**. If one stage runs on coffea-casa / REANA and the
  next on ml.cern.ch, you need a shared storage seam — usually an EOS
  project area or `reana-client download` + re-upload. Name the seam
  in the recommendation.
- **Auth escalation**. Recipes start from the narrowest auth tier
  and add privileges only where needed (public → CERN SSO → VOMS
  proxy). Don't push grid credentials on a user who can stay public.
