---
name: physlite-basics
description: Use when the user needs to OPEN an ATLAS DAOD_PHYSLITE file with `uproot` / `awkward`, list its branches, reconstruct calibrated objects (electrons, muons, photons, taus, small-R jets, large-R jets, MET, trigger decisions), or apply MC normalisation. Assumes a public HTTPS or XRootD URI such as `root://eospublic.cern.ch/...` from `atlas_get_urls` or `cod_list_files`. Does NOT cover the older flat 13 TeV reduced ntuples (use the matching tutorial via `atlas-notebooks`), CMS NanoAOD or MiniAOD, or sample discovery (use `atlas-opendata`). Disambiguator phrase: PHYSLITE branch reader.
data_scope: open
---

## Scope

Use this skill when the user is handling **DAOD_PHYSLITE** files
(the default "physics-lite" derivation format of the 2024+ ATLAS Open
Data releases). For the older 13 TeV reduced ntuples used by the
uproot_python tutorials in
`atlas-outreach-data-tools/notebooks-collection-opendata`, this skill
is **not** the right one — those are flat ntuples with bespoke
branches; point users at the relevant notebook directly via
`atlas-notebooks`.

If the user needs a DSID or cross-section, use `atlas-opendata`.
If the user needs a portal file URI, use `cern-opendata`.

## What PHYSLITE is

- ATLAS's official slimmed-down derivation designed for analysis
  without the full xAOD framework.
- Ships calibrated analysis-level objects: electrons, muons, photons,
  taus, small-R jets, large-R jets, MET, trigger decisions, event
  info.
- Readable with uproot (or xAOD via Athena; Open Data users should
  prefer uproot).
- Companion tutorial:
  `for-research/physlite_tutorial.ipynb` in
  atlas-outreach-data-tools/notebooks-collection-opendata.

## Reading a file

Given a URI from `atlas_get_urls(protocol='https')` or from
`cod_list_files`:

```python
import uproot
f = uproot.open("https://opendata.cern.ch/record/.../DAOD_PHYSLITE.root")
t = f["CollectionTree"]
```

The interesting physics objects live under `AnalysisElectronsAuxDyn`,
`AnalysisMuonsAuxDyn`, `AnalysisJetsAuxDyn`, `AnalysisPhotonsAuxDyn`,
`AnalysisTauJetsAuxDyn`, `MET_Core_AnalysisMETAuxDyn`, with kinematics
in `pt`, `eta`, `phi`, `m` (in MeV — watch the units).

## Common branches

| Collection | Typical branches | Notes |
|---|---|---|
| `AnalysisElectronsAuxDyn` | `pt`, `eta`, `phi`, `m`, `charge` | Calibration applied |
| `AnalysisMuonsAuxDyn` | `pt`, `eta`, `phi`, `charge`, `muonType`, `quality` | `muonType == 0` is Combined |
| `AnalysisJetsAuxDyn` | `pt`, `eta`, `phi`, `m`, `DFCommonJets_jetClean_LooseBad` | AntiKt4EMPFlow |
| `AnalysisPhotonsAuxDyn` | `pt`, `eta`, `phi`, `m` | Use with ID flags |
| `MET_Core_AnalysisMETAuxDyn` | `mpx`, `mpy`, `sumet` | `MET = sqrt(mpx^2 + mpy^2)` |
| `EventInfoAuxDyn` | `mcEventWeights`, `runNumber`, `eventNumber` | First element of `mcEventWeights` is the nominal `mcWeight` |

Units are **MeV** throughout PHYSLITE. Convert to GeV before
plotting.

## MC normalisation

Use the formula (always — do not hide it in a helper):

```
weight = cross_section_pb * 1000 * kFactor * genFiltEff * mcWeight / sumOfWeights * luminosity_fb
```

Get the per-sample terms from the `atlasopenmagic` MCP:
- `atlas_get_metadata(dsid)` → `cross_section_pb`, `kFactor`,
  `genFiltEff`, `sumOfWeights`.
- `mcWeight` is per-event, from `EventInfoAuxDyn.mcEventWeights[0]`.
- `luminosity_fb` comes from the release (e.g. 36.1 fb⁻¹ for the
  old Hyy tutorial, 140 fb⁻¹ for Run 2 full).

## Procedure

1. Get the URI for the sample with
   `atlas_get_urls(dsid, protocol='https')` (or `protocol='root'` for
   XRootD).
2. Open with `uproot.open`.
3. Read the branches you need with `t.arrays([...], library='ak')`.
4. Convert MeV → GeV.
5. Compute the per-event weight using the formula above.
6. Fill histograms with `hist` / `boost_histogram`, plot with
   `mplhep.style.ATLAS`.

## Pitfalls

- Units are **MeV**, not GeV. Most published plots divide by 1000.
- `mcEventWeights` is a **vector**, nominal is index `[0]`. The rest
  are systematic variations.
- `sumOfWeights` is a **dataset-level** quantity. Read it once from
  `atlas_get_metadata`, not per-event.
- Data files don't have `mcEventWeights`; guard with an
  `is_data` flag.
- For trigger decisions you need `TrigMatch` info which is **not**
  in PHYSLITE auxiliaries — fall back to the reduced 13 TeV ntuples
  if the user wants detailed trigger studies.

## Verification

A successful use of this skill ends with the user having:
1. Opened a PHYSLITE file with `uproot.open`.
2. Extracted at least one kinematic array in GeV.
3. Printed (or plotted) a weighted distribution using the
   normalisation formula above.
