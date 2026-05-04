---
name: read-publication
description: Use when the user gives you a PDF path, arXiv ID (`2401.12345` or `arXiv:2401.12345`), INSPIRE record id (`recid:1234567` or `inspire-hep:1234567`), DOI (`10.1103/...`), or HEP paper URL and wants extracted content — abstract, measured cross-section / branching ratio / mass, conditions, cuts, fit method. Routes to the right retrieval (`pdftotext` for local PDFs; INSPIRE + arXiv APIs via `WebFetch` for IDs and URLs). Always cites per AGENTS.md rule 5. Does NOT cover PDG canonical particle constants (use `pdg-lookup`), HEPData numerical tables for re-fitting (use `hepdata`), CERN service operator docs (use `cern-docs`), or Open Data dataset records (use `cern-opendata` or `atlas-opendata`). Disambiguator phrase: published-HEP-result extractor.
data_scope: both
---

# read-publication — extract published HEP results from a paper

This skill turns a paper reference (PDF, arXiv ID, INSPIRE record, DOI, URL)
into extracted content the user can use — abstract, measured values,
experimental conditions — with a citation per AGENTS.md rule 5.

## Scope

Load this skill when the user provides any of:

- A local PDF path (typically EOS, AFS, lxplus home, or SWAN workspace)
- An arXiv ID (`2401.12345`, with or without `arXiv:` prefix; old-style
  `hep-ex/0501001` also valid)
- An INSPIRE record id (`recid:1234567`, `inspire-hep:1234567`, or a
  `inspirehep.net/literature/1234567` URL)
- A DOI (`10.1103/PhysRevLett.130.041801`, with or without `https://doi.org/`)
- A journal or preprint URL (`link.aps.org/doi/...`, `arxiv.org/abs/...`,
  `link.springer.com/article/...`, etc.)

Do NOT load this skill for:

- **PDG canonical constants** (electron mass, Z width, B branching ratios
  from PDG average) → `pdg-lookup`.
- **Numerical tables for re-fitting** (HEPData-attached YAML / ROOT / CSV)
  → `hepdata`.
- **CERN service operator docs** (SWAN, HTCondor, Athena how-tos) → `cern-docs`.
- **Open Data primary dataset records** (CMS / ATLAS / LHCb releases on
  the portal) → `cern-opendata` or `atlas-opendata`.

## Input-type detection

Before retrieving, identify which input you have:

| Input shape | Type | Retrieval path |
|---|---|---|
| Path starts with `/` and ends `.pdf` | Local PDF | `pdftotext` via Bash (per AGENTS.md PDF guideline) |
| `\d{4}\.\d{4,5}` or `arXiv:...` | arXiv ID | INSPIRE API by arxiv eprint, then arXiv abstract API |
| `recid:\d+` / `inspire-hep:\d+` / `inspirehep.net/literature/\d+` | INSPIRE recid | INSPIRE API by id |
| `10\.\d{4,}/...` (DOI) | DOI | INSPIRE API by doi query |
| `https?://...` (other) | Paper URL | `WebFetch` directly, then INSPIRE lookup if a metadata anchor is needed |

If multiple inputs are given (e.g. arXiv ID + a path to a local PDF copy),
prefer the local PDF for content + INSPIRE for metadata + citation.

## Retrieval recipes

### Local PDF

Follow the AGENTS.md PDF text extraction guideline (`pdftotext` first,
`pypdf` fallback). Capture stdout into your reasoning context. Do not
paste the full extracted text into the user reply unless asked — extract
the requested content (abstract, table value, conditions) and cite the
file path.

### arXiv ID

1. INSPIRE: `WebFetch https://inspirehep.net/api/literature?q=arxiv:<id>&fields=titles,authors,abstracts,arxiv_eprints,dois,inspire_id`
2. If the user wants the abstract, INSPIRE's `abstracts[].value` is enough.
3. If the user wants a measured value or table, fetch the arXiv PDF:
   `WebFetch https://arxiv.org/pdf/<id>` — but note that `WebFetch` returns
   markdown-rendered text, not always reliable for tables. For tables, ask
   the user whether to download the PDF locally and run `pdftotext`.

### INSPIRE record id

`WebFetch https://inspirehep.net/api/literature/<recid>?fields=titles,authors,abstracts,dois,arxiv_eprints,publication_info`

### DOI

1. INSPIRE: `WebFetch https://inspirehep.net/api/literature?q=doi:<doi>&fields=...`
2. If INSPIRE has no record (rare for HEP), `WebFetch https://doi.org/<doi>` directly.

### Paper URL

`WebFetch <url>` for content. Resolve to INSPIRE recid in parallel for
citation: `WebFetch https://inspirehep.net/api/literature?q=url:<url>`.

## HEP extraction heuristics

When the user asks "what cross-section did they measure":

- Search the extracted text for `Table` headings — published cross-sections
  are almost always tabulated.
- Search for fiducial / total / differential cross-section keywords plus
  `± stat ± syst` patterns.
- Search for `√s = N TeV` or `at √s =` to confirm the centre-of-mass energy.
- Search for the analysis luminosity (`L = N fb⁻¹` or `integrated
  luminosity of N fb⁻¹`).
- If the paper has a HEPData submission attached (search INSPIRE response
  for `external_system_identifiers` with `schema: HEPData`), tell the user
  HEPData has the table programmatically and offer to switch to the
  `hepdata` skill.

## Citation

Per AGENTS.md rule 5, every quoted value must come with a source. Format:

> The fiducial cross-section is **σ_fid = 2.85 ± 0.21 pb** (Table 4),
> measured at √s = 13 TeV with 139 fb⁻¹.
> [arXiv:2401.12345 / INSPIRE recid 1234567 / DOI 10.1103/...]

Pick whichever identifier the user provided as primary; include the
INSPIRE recid as secondary if available.

## Failure recovery

- INSPIRE returns 0 hits for an arxiv id → arXiv abstract API directly,
  warn the user that INSPIRE has no record (uncommon for HEP, may be a
  preprint not yet ingested).
- `pdftotext` fails on a local PDF → fall through per AGENTS.md guideline.
- DOI 404s → likely the DOI is mis-typed; show the user what you tried.

Never invent a value. If extraction fails, report the failure and ask
the user to provide the value or a different input.
