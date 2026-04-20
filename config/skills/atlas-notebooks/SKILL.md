---
name: atlas-notebooks
description: Index of the public ATLAS Open Data outreach notebooks from atlas-outreach-data-tools/notebooks-collection-opendata. Load this skill when the user asks "how do I run X notebook", "which notebook teaches Y", or wants to pick a runtime (Binder / Colab / SWAN / Docker) for an ATLAS Open Data tutorial.
---

## Scope

Use this skill for **notebook discovery and runtime selection** in the
public repo
https://github.com/atlas-outreach-data-tools/notebooks-collection-opendata.
If the user has already picked a Standard Model walkthrough, prefer
the `sm-analyses` skill for the physics-level procedure. If the user
needs to look up ATLAS MC metadata to feed a notebook, use
`atlas-opendata`.

This skill does **not** drive an MCP. It is a curated index of
existing material. Cite the GitHub path whenever you name a notebook.

## Repository layout (as of April 2026)

- `13-TeV-examples/uproot_python/` — Python + uproot notebooks
  (no ROOT required). The main tutorial set.
- `13-TeV-examples/rdataframe/` — RDataFrame (PyROOT) variants of
  the Hyy analysis.
- `13-TeV-examples/pyroot/` — minimal PyROOT examples
  (histogram, Z mass, Hyy, kinematics).
- `13-TeV-examples/cpp/` — C++ ROOT variants.
- `8-TeV-examples/` — legacy 8 TeV tutorials.
- `for-research/` — advanced material (PHYSLITE tutorial,
  event-generation tutorial, Rivet, fake-rate estimation,
  phoenix viewer, public likelihoods).

## Notebook map (13-TeV-examples/uproot_python/)

| File | Topic | Skill to pair with |
|---|---|---|
| `IntroToEducationAndOutreachOD.ipynb` | Orientation for new users | — |
| `Find_the_Z.ipynb` | Z → μμ peak reconstruction | sm-analyses |
| `HZZAnalysis.ipynb` | H → ZZ → 4ℓ rediscovery | sm-analyses |
| `CoffeaHZZAnalysis.ipynb` | Same, using coffea | sm-analyses |
| `HyyAnalysis.ipynb` | H → γγ, 36.1 fb⁻¹ | sm-analyses |
| `HbbAnalysis.ipynb` | H → bb (advanced) | sm-analyses |
| `Hmumu.ipynb` | H → μμ | sm-analyses |
| `ttbar_analysis.ipynb` | tt̄ pair production | sm-analyses |
| `WZ3l_Analysis.ipynb` | WZ → 3ℓ + ν | sm-analyses |
| `GravitonAnalysis.ipynb` | BSM graviton search | — |
| `Dark_Matter_Machine_Learning.ipynb` | ML for DM | — |
| `HZZ_BDT_demo.ipynb`, `HZZ_NeuralNet_demo.ipynb` | ML on H→ZZ | — |
| `MetadataTutorial.ipynb` | Cross-sections and weights | atlas-opendata |
| `systematics_notebook.ipynb` | Systematic uncertainties | — |
| `detector_acceptance_and_efficiency.ipynb` | Acceptance vs efficiency | — |
| `Fluctuations.ipynb` | Statistical fluctuations | — |
| `NCB.ipynb` | Non-collision backgrounds | — |

## Notebook map (for-research/)

| File | Topic |
|---|---|
| `physlite_tutorial.ipynb` | DAOD_PHYSLITE format (pair with `physlite-basics`) |
| `OpenEvgenTutorial.ipynb` | Event generation tutorial |
| `rivet.ipynb` | Rivet for generator-level analysis |
| `FakeRateEstimation/` | Fake-lepton estimation |
| `public-likelihoods/` | pyhf likelihoods |
| `phoenix/` | Phoenix event display |
| `limitations/` | Documented limits of the dataset |

## Procedure

1. Identify the physics process or technique the user cares about.
2. Pick the notebook from the tables above. Quote the path exactly
   (`13-TeV-examples/<subdir>/<name>.ipynb`).
3. Pick the runtime (see next section).
4. List the Python dependencies (uproot, awkward, matplotlib,
   mplhep, hist, coffea, pyhf as applicable). For
   `for-research/physlite_tutorial.ipynb`, there is a dedicated
   `physlite_tutorial_requirements.txt`.
5. If the user hasn't cloned the repo, point them at
   `git clone https://github.com/atlas-outreach-data-tools/notebooks-collection-opendata.git`.

## Runtime selection

The README in the upstream repo advertises all five of these for the
13 TeV examples. Default order of recommendation:

| Runtime | When to recommend |
|---|---|
| **Binder** | Default for first-time users. Zero local install. Warn that the "not trusted" button must be clicked for interactive histograms. |
| **Google Colab** | User wants GPU (e.g. for the ML notebooks) or already lives in Colab. |
| **SWAN** (swan.cern.ch) | User has a CERN account. |
| **GitHub Codespaces** | Developer workflow, wants a persistent environment. |
| **Docker** | Local reproducibility. `docker-compose.yml` at the repo root. |

## Pitfalls

- The outreach notebooks use a **reduced 13 TeV ntuple format**, not
  raw PHYSLITE, except for `for-research/physlite_tutorial.ipynb`
  which does use PHYSLITE. Don't confuse the two.
- File paths are **read-only URIs**. Users don't need Rucio.
- `HZZ_BDT_demo.ipynb` and `HZZ_NeuralNet_demo.ipynb` are not
  self-contained ML tutorials — they assume `HZZAnalysis.ipynb`
  has been run first.

## Verification

A successful use of this skill ends with the user knowing:
1. The exact notebook path in the outreach repo.
2. One recommended runtime with a concrete click-through (Binder
   badge / Colab URL / SWAN share).
3. The Python packages they'll need, if running locally.
