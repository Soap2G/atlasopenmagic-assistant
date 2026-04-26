---
name: sm-analyses
description: Use when the user names a Standard Model process and wants to "rediscover" it with the public ATLAS Open Data — Z→ll, H→ZZ→4l, H→γγ, H→μμ, H→bb, t-tbar, or WZ→3l+ν. Pairs the process to its docs section in `13TeV25Doc/StandardModel` and its notebook in `notebooks-collection-opendata/13-TeV-examples/uproot_python/`. Does NOT cover BSM searches, generic notebook indexing by filename (use `atlas-notebooks`), or analysis-code authoring (use `physlite-basics` or the `analysis` agent). Disambiguator phrase: SM walkthrough by process.
data_scope: open
---

## Scope

Use this skill for the SM walkthrough chapters at
https://opendata.atlas.cern/docs/13TeV25Doc/StandardModel and their
corresponding notebooks in
`atlas-outreach-data-tools/notebooks-collection-opendata/13-TeV-examples/uproot_python/`.

If the user has a different process (e.g. a BSM search, a ML example,
or a technical tutorial), use `atlas-notebooks` instead.

## Walkthrough table

| Process | Docs section | Notebook |
|---|---|---|
| Z → μμ (and Z → ee / other SM extensions) | Find the Z boson | `Find_the_Z.ipynb` |
| H → ZZ* → 4ℓ | Higgs to ZZ | `HZZAnalysis.ipynb` |
| H → γγ | Higgs to γγ | `HyyAnalysis.ipynb` |
| H → μμ | Higgs to Muon–Antimuon | `Hmumu.ipynb` |
| H → bb | Higgs to bb | `HbbAnalysis.ipynb` |
| tt̄ | Top–Antitop | `ttbar_analysis.ipynb` |
| WZ → 3ℓ + ν | WZ to three leptons | `WZ3l_Analysis.ipynb` |

All seven notebooks live in
`13-TeV-examples/uproot_python/` of the outreach repo.

## Common procedure

For any of the seven walkthroughs:

1. Read the docs section (quote the URL). It gives the physics
   motivation, the event selection, and the expected plot.
2. Open the matching notebook (`13-TeV-examples/uproot_python/<file>.ipynb`)
   in the user's runtime of choice (via the `atlas-notebooks` skill).
3. Identify the MC samples the notebook needs. Use
   `atlas_match_metadata` with keywords / processes from the docs
   (e.g. `Zee`, `Zmumu`, `ttbar`, `Higgs`, `ZZ`, `WZ`).
4. Confirm the release via `atlas_get_current_release` — the 2025
   SM docs correspond to the `2024r-pp` or `2025r-evgen-13tev`
   releases; use the one the notebook header specifies.
5. Reproduce the expected plot. Compare the position of the peak
   with the known mass (91.2 GeV Z, 125 GeV H, 172.5 GeV t).

## Per-walkthrough notes

### Find_the_Z (Z → μμ)
Selection: 2 opposite-sign muons, dimuon invariant mass.
Expected peak at ~91.2 GeV. Extensions suggested in the docs: Z→ee,
J/ψ, Υ by changing the mass window.

### HZZAnalysis (H → ZZ* → 4ℓ)
Selection: 4 leptons, 2 same-flavour opposite-sign pairs, m_Z1 near
91 GeV, m_Z2 in [12,60] GeV. Expected narrow peak at m_4l ≈ 125 GeV.
Companion coffea-based version:
`CoffeaHZZAnalysis.ipynb`. The ML demos
(`HZZ_BDT_demo.ipynb`, `HZZ_NeuralNet_demo.ipynb`) build on this
output.

### HyyAnalysis (H → γγ)
Uses 36.1 fb⁻¹ (per the docs). Selection: 2 isolated photons with
tight ID, m_γγ in [105,160] GeV. Fit the m_γγ spectrum with a
continuum background + Gaussian signal at 125 GeV. RDataFrame
variants live in `13-TeV-examples/rdataframe/RDataFrame_Hyy.ipynb`
and `RDataFrame_Hyy_SimpleExample.ipynb`.

### Hmumu (H → μμ)
Very suppressed branching ratio; the notebook teaches signal
extraction in a large background. Peak at 125 GeV on a steeply
falling DY+jets continuum.

### HbbAnalysis (H → bb)
Advanced — the docs flag this as attempting to find H → bb. Uses
b-tagged jets and requires MVA techniques. Not a good first
walkthrough.

### ttbar_analysis (tt̄)
Lepton + jets channel. Selection: 1 lepton, ≥4 jets with ≥2 b-tags,
MET. Expected shape in jet multiplicity and b-tag multiplicity.

### WZ3l_Analysis (WZ → 3ℓν)
Selection: 3 leptons, one opposite-sign same-flavour pair near 91
GeV (the Z), remaining lepton + MET forms the W transverse mass.

## Pitfalls

- Notebook headers sometimes reference older releases (e.g.
  `2020e-13tev`). Check with `atlas_get_current_release` and
  `atlas_set_release` before pulling sample metadata — DSIDs change
  across releases.
- The ML demos (`HZZ_BDT_demo`, `HZZ_NeuralNet_demo`) **are not**
  teaching ML from scratch; they assume the user already has the
  `HZZAnalysis.ipynb` ntuples.
- Hbb is not a clean "rediscovery" in the outreach release; don't
  over-promise a peak.
- Luminosity numbers: 36.1 fb⁻¹ for older Hyy; ~140 fb⁻¹ for Run 2
  full. Check the docs section, not the notebook, to get the
  authoritative number.

## Verification

A successful use of this skill ends with the user:
1. Open on the correct docs page and matching notebook.
2. Aware of the MC samples to query (via `atlas_match_metadata`).
3. Reproducing the expected peak / distribution within a reasonable
   tolerance of the docs figure.
