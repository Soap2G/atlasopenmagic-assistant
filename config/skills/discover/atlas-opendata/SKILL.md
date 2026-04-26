---
name: atlas-opendata
description: Use when the user has an ATLAS DSID, `physics_short` name, or ATLAS Open Data release tag (`2024r-pp`, `2025r-evgen-13tev`) and needs file URLs, cross-sections, k-factors, filter efficiencies, sumOfWeights, or MC weight metadata. Backed by the `atlasopenmagic` MCP. Operates on ATLAS Open Data only — for collaboration-internal datasets use `rucio`; for non-ATLAS portal records identified by `recid` or DOI use `cern-opendata`. Disambiguator phrase: atlasopenmagic DSID resolver.
data_scope: open
---

## Scope

Use this skill only when the user is clearly working with ATLAS Monte
Carlo samples or an ATLAS Open Data release. For non-ATLAS experiments,
portal-wide record searches, or records identified by `recid` / DOI /
title, use the sibling `cern-opendata` skill (backed by the
`cernopendata` MCP). The two servers cooperate — you can start from a
portal record via `cod_*` tools and drop into ATLAS-specific metadata
with `atlas_*` tools when the analysis calls for it.

## MCP Tools Available

The `atlasopenmagic` MCP server provides these tools (prefixed with `atlasopenmagic_`):

### Discovery
- `atlas_available_releases` — List all available data releases
- `atlas_get_current_release` — Show the currently active release
- `atlas_set_release` — Switch to a different release
- `atlas_available_datasets` — List all datasets in the current release
- `atlas_available_skims` — List available skim types
- `atlas_available_keywords` — List physics keywords for filtering

### Metadata
- `atlas_get_metadata` — Get metadata for a specific dataset (by DSID or physics_short)
- `atlas_get_metadata_fields` — List all available metadata fields
- `atlas_get_all_info` — Get comprehensive info for a dataset
- `atlas_match_metadata` — Search datasets by metadata field values or keywords

### File URLs
- `atlas_get_urls` — Get ROOT file URLs for a dataset (protocols: root, https, eos)

### Weights
- `atlas_get_weights` — Get MC weight metadata for a dataset
- `atlas_get_all_weights_for_release` — Get weight metadata for all datasets in a release

## Workflow

1. Check/set the release with `atlas_get_current_release` or `atlas_set_release`
2. Find datasets with `atlas_match_metadata` (search by keywords, process, generator) or `atlas_available_datasets`
3. Get details with `atlas_get_metadata` or `atlas_get_all_info`
4. Get file URLs with `atlas_get_urls`
5. For MC weights/systematics, use `atlas_get_weights`

## ATLAS Open Data Quick Reference

### Releases

| Release              | Description                                              |
|----------------------|----------------------------------------------------------|
| 2016e-8tev           | 2016 education release, 8 TeV pp collisions              |
| 2020e-13tev          | 2020 education release, 13 TeV pp collisions             |
| 2024r-pp             | 2024 research release, proton-proton collisions          |
| 2024r-hi             | 2024 research release, heavy-ion collisions              |
| 2025e-13tev-beta     | 2025 education beta release, 13 TeV pp collisions        |
| 2025r-evgen-13tev    | 2025 research event-generation release, 13 TeV           |
| 2025r-evgen-13p6tev  | 2025 research event-generation release, 13.6 TeV         |

### Datasets

Each Monte Carlo sample is identified by a numeric **dataset number** (DSID), e.g. `301204`, and a human-readable **physics_short** name, e.g. `Sh_2211_Zee_maxHTpTV2_BFilter`.

### Physics Short Name Convention

The physics_short packs generator, tune/PDF, process, and filters into a structured name. Parts are separated by underscores.

**Part 1 — Generator abbreviations (always first):**

| Abbrev | Generator       | Abbrev | Generator       |
|--------|-----------------|--------|-----------------|
| Sh     | Sherpa          | H7     | Herwig7         |
| Ph     | Powheg          | Ag     | Alpgen          |
| Py8    | Pythia8         | EG     | EvtGen          |
| MG     | MadGraph (LO)   | PG     | ParticleGun     |
| aMC    | aMC@NLO         | HepMC  | HepMC files     |

**Part 2 — Tune / PDF / Sherpa version:**
- Tunes: A14, AZ, AZNLO, H7UE
- Sherpa version: `222` = 2.2.2, `2211` = 2.2.11, `2212` = 2.2.12
- PDFs: NNPDF30NNLO, NNPDF23LO, MSTW2008LO, CTEQ6L1

**Remaining parts — Process and filters:**

Process abbreviations:
- `tchan`/`schan` = t/s-channel
- `Zee` = Z->ee, `Zmumu` = Z->mumu, `Wenu` = W->enu
- `incl` = inclusive, `dil` = di-lepton, `nonallhad` = at least one lepton, `allhad` = all-hadronic

Production features:
- `FxFx` = FxFx merging, `DS`/`DR` = diagram subtraction/removal

Filters (usually at the end):
- `BFilter` = b-quark filter, `BVetoCFilter` = no b, has c, `BVetoCVeto` = no b or c
- These three heavy-flavor filters should be combined for complete background
- `maxHTpTV2` = HT and pT(V) filter, `MET200` = 200 GeV MET filter

**Example:** `Sh_2211_Zee_maxHTpTV2_BFilter` = Sherpa 2.2.11, Z->ee, maxHTpTV2 filter, b-quark filter

### Skims

Pre-filtered subsets: `exactly4lep`, `3lep`, etc. Use `noskim` for the full dataset.

### Metadata Fields

Core: `dataset_number`, `physics_short`, `e_tag`
Physics: `cross_section_pb`, `genFiltEff`, `kFactor`, `nEvents`, `sumOfWeights`, `sumOfWeightsSquared`
Generation: `process`, `generator`, `keywords`, `description`, `GenTune`, `PDF`, `CoMEnergy`
Files: `file_list`, `skims` (each with `skim_type` and `file_list`)

### File URL Protocols

- `root` — XRootD streaming (default, best for analysis)
- `https` — Web-accessible via opendata.cern.ch
- `eos` — EOS POSIX mount path

### Luminosity Weighting Formula

For MC normalisation:
```
weight = cross_section_pb * 1000 * kFactor * genFiltEff * mcWeight / sumOfWeights * luminosity_fb
```
