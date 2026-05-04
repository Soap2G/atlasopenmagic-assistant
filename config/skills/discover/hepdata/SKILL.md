---
name: hepdata
description: Use when the user wants the numerical tables, ROOT files, or YAML data attached to a published HEP measurement, identified by HEPData submission ID (`ins1234567`, `123/v2`), INSPIRE record id, paper DOI, or paper title — typically because they want to re-fit, plot, or run systematics studies on the published measurement. Routes to https://www.hepdata.net/ via WebFetch and the HEPData REST API. Returns table URLs (YAML, ROOT, CSV) suitable for downstream `pyhf`, `pandas`, or `uproot`. Does NOT cover the paper's narrative or the headline measured value (use `read-publication`), PDG canonical constants (use `pdg-lookup`), or Open Data primary datasets (use `cern-opendata` or `atlas-opendata`). Disambiguator phrase: HEPData published-tables retrieval.
data_scope: both
---

# hepdata — published HEP tables for re-fitting

HEPData hosts the numerical tables, covariance matrices, and ROOT inputs
that LHC papers publish alongside their results. Use this skill when the
user wants to *consume* those tables (re-fit, plot, systematics study) —
not when they want the headline measurement value (that's `read-publication`).

## Scope

Load this skill when the user provides any of:

- A HEPData submission id (`ins1234567` — INSPIRE-keyed, or `123/v2` —
  HEPData-internal versioned id)
- An INSPIRE record id (`recid:1234567` or `inspire-hep:1234567`)
- A paper DOI (`10.1103/...`, `10.1007/JHEP...`)
- A paper title (exact match preferred — HEPData search is fuzzy)

…and they want the tabulated data, not the prose result.

Do NOT load this skill for:

- **The headline measured value or the paper narrative** → `read-publication`.
- **PDG canonical constants** → `pdg-lookup`.
- **Open Data primary datasets** (CMS / ATLAS / LHCb data releases on
  `opendata.cern.ch`) → `cern-opendata`.
- **ATLAS Monte Carlo metadata by DSID** → `atlas-opendata`.

## HEPData URL patterns

| Pattern | Meaning |
|---|---|
| `https://www.hepdata.net/record/ins<inspire-recid>` | INSPIRE-keyed (most common) |
| `https://www.hepdata.net/record/<hepdata-id>` | HEPData-internal id |
| `https://www.hepdata.net/record/ins<id>?version=N` | Specific version |
| `https://www.hepdata.net/record/ins<id>?format=json` | Machine-readable record metadata |
| `https://www.hepdata.net/search/?q=<query>&format=json` | Search by title / DOI / keyword |

## INSPIRE → HEPData mapping

If the user gives you an INSPIRE recid, the HEPData URL is
`https://www.hepdata.net/record/ins<recid>`. This is 1:1 by construction.

If the user gives you a DOI or title, resolve it to an INSPIRE recid first
via the `read-publication` retrieval recipe (or run INSPIRE search yourself),
then build the HEPData URL.

## Choosing a format

Each HEPData record exposes its tables in multiple formats. Pick by use case:

| Format | URL suffix | When to use |
|---|---|---|
| YAML | `?format=yaml` (per-table) | Most portable; human-readable; pyhf-friendly |
| ROOT | `?format=root` | When the user works in ROOT / uproot already |
| CSV | `?format=csv` | Quick `pandas.read_csv` integration |
| JSON | `?format=json` | Programmatic record introspection |

Default recommendation: YAML for new analysis pipelines, ROOT for ATLAS-
internal habits.

## Retrieval recipe

1. **Resolve the input** to an INSPIRE recid or HEPData id.
2. `WebFetch https://www.hepdata.net/record/ins<recid>?format=json` to get
   the record metadata. Look at:
   - `data_tables[].name` and `.description` to pick the right table(s).
   - `data_tables[].data` for the per-table data URL.
3. Return per-table URLs to the user with table names and descriptions.
4. Suggest the right downstream pipeline (`pyhf` for likelihoods,
   `pandas.read_csv` for tabular extraction, `uproot.open` for ROOT inputs).

## Common downstream pipelines

After retrieving HEPData tables:

- **Re-fit a likelihood** → use `pyhf` if the record exposes `workspace.json`
  (HistFactory standard; ATLAS publishes these for many measurements).
- **Plot a spectrum** → `pandas.read_csv` + `matplotlib` / `mplhep`.
- **Combine with another measurement** → covariance matrices are usually
  in a separate table; flag this to the user.

## Failure recovery

- HEPData has no record for an INSPIRE recid → not every paper publishes
  to HEPData. Tell the user; offer to extract the value from the paper via
  `read-publication` instead (lossy: just the published number, no
  uncertainties propagated).
- Search returns multiple records → present top 3 hits with title +
  experiment + year, ask the user to disambiguate.
- A specific format isn't available for a table → fall back to YAML
  (always available).
