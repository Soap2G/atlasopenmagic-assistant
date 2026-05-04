---
name: pdg-lookup
description: Use when the user asks for a canonical Particle Data Group value — particle mass, lifetime, branching ratio, decay width, magnetic moment, mixing parameter, charge, spin, or any quoted "PDG average" constant. Backed by https://pdg.lbl.gov/ via WebFetch (HTML pdgLive pages and the PDG REST API where available). Always cites the PDG record URL and edition year. Does NOT cover ATLAS Monte Carlo metadata (use `atlas-opendata`), measured values from a specific paper (use `read-publication`), HEPData tabulated measurements (use `hepdata`), or conceptual physics explanations of why a particle has the value it does (use the `tutor` agent). Disambiguator phrase: PDG particle data group lookup.
data_scope: both
---

# pdg-lookup — canonical particle physics constants

This skill is the only correct path for quoting a particle mass, lifetime,
branching ratio, or any other PDG-averaged constant. Critical rule 5
forbids quoting these from training-data memory.

## Scope

Load this skill when the user asks for a canonical particle physics
constant — values that appear in the PDG Review and pdgLive listings.

Examples:
- "What is the Z mass?"
- "Look up the muon lifetime."
- "What's BR(B0 → K*0 μ+ μ-)?"
- "What's the τ → πν branching fraction?"

Do NOT load this skill for:

- **A measurement from a specific paper or experiment** → `read-publication`.
- **Numerical tables attached to a published measurement** → `hepdata`.
- **ATLAS / CMS Monte Carlo cross-section metadata** → `atlas-opendata`
  (DSID, generator-level cross-section, k-factor — not the same as
  PDG-averaged values).
- **Conceptual explanations** ("why does the Z have a mass") → `tutor` agent.

## The always-cite rule

Every value quoted from this skill MUST include:

1. The numerical value with units.
2. The PDG uncertainty (statistical + systematic combined, as PDG presents it).
3. The PDG record URL.
4. The PDG edition year (currently **2024**; bump when the next review ships).

Example reply:

> The Z boson mass is **m_Z = 91.1880 ± 0.0020 GeV** (PDG 2024).
> Source: https://pdg.lbl.gov/2024/listings/rpp2024-list-z-boson.pdf

This skill exists specifically to close the rule 5 loophole. **Never quote
a particle constant without running this skill or a comparable tool call.**

## PDG retrieval

The PDG offers several access surfaces; pick the cheapest that answers the
question:

| Surface | URL pattern | Use for |
|---|---|---|
| pdgLive listing pages (HTML) | `https://pdg.lbl.gov/2024/listings/rpp2024-list-<particle>.pdf` | Full review entries with averages and inputs |
| pdgLive summary tables (HTML) | `https://pdg.lbl.gov/2024/tables/rpp2024-sum-<group>.pdf` | Quick cross-particle comparisons |
| PDG Booklet PDF | `https://pdg.lbl.gov/2024/booklet/rpp2024-booklet.pdf` | Bulk reading offline |
| PDG REST API (where available) | `https://pdgapi.lbl.gov/...` | Programmatic single-value lookup |

The REST API is evolving and not all values are exposed yet. If a value is
missing from the API, fall through to the relevant listing PDF and extract
via the v1.6.0 PDF guideline (`pdftotext` over the listing).

## Common particle URL cheatsheet

(Not the values — the URLs. The values come from a fresh fetch every time.)

| Particle | Listing URL |
|---|---|
| Z boson | `https://pdg.lbl.gov/2024/listings/rpp2024-list-z-boson.pdf` |
| W boson | `https://pdg.lbl.gov/2024/listings/rpp2024-list-w-boson.pdf` |
| Higgs boson | `https://pdg.lbl.gov/2024/listings/rpp2024-list-higgs-boson.pdf` |
| Top quark | `https://pdg.lbl.gov/2024/listings/rpp2024-list-t-quark.pdf` |
| Muon | `https://pdg.lbl.gov/2024/listings/rpp2024-list-muon.pdf` |
| Tau | `https://pdg.lbl.gov/2024/listings/rpp2024-list-tau.pdf` |
| Pion (π±) | `https://pdg.lbl.gov/2024/listings/rpp2024-list-pi-plus-minus.pdf` |
| B0 | `https://pdg.lbl.gov/2024/listings/rpp2024-list-B0.pdf` |
| B± | `https://pdg.lbl.gov/2024/listings/rpp2024-list-B-plus-minus.pdf` |

For particles not in this cheatsheet, search the PDG index page first:
`https://pdg.lbl.gov/2024/listings/contents_listings.html`.

## Edition bump procedure

When a new PDG Review is published (typically every two years, July):

1. Update the year in URL examples above (`2024` → `2026`).
2. Update the "PDG 2024" citation format string to the new edition.
3. Update the description disambiguator if needed.
4. Bump VERSION (patch).
