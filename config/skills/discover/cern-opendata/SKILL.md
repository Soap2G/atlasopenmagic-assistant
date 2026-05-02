---
name: cern-opendata
description: Use when the user has a CERN Open Data `recid`, DOI, or exact record title and needs portal-level metadata, file URIs, container images, or supplementary files across CMS, ATLAS, LHCb, ALICE, or OPERA. Backed by the `cernopendata` MCP at opendata.cern.ch (records, files, glossary). Does NOT cover ATLAS Monte Carlo metadata by DSID or `physics_short` (use `atlas-opendata`), collaboration-internal datasets (use `rucio`), or canonical CERN service / ATLAS-software documentation (use `cern-docs` for SWAN, HTCondor, Cloud, ML@CERN, Athena docs). Disambiguator phrase: opendata.cern.ch recid resolver.
data_scope: open
---

## Scope

Use this skill whenever the user is working with the portal itself —
browsing, resolving DOIs, fetching record metadata, or listing the files
attached to a record. The `cernopendata` MCP is portal-wide: it does not
know about ATLAS DSIDs, `physics_short` names, k-factors, or filter
efficiencies. For those, switch to (or also load) the `atlas-opendata`
skill.

The two skills cooperate. A typical flow is:
1. Use `cod_resolve_record` / `cod_get_metadata` to locate a portal
   record (e.g. an ATLAS analysis example or a CMS primary dataset).
2. Use `cod_list_files` to get the file URIs attached to that record.
3. If the workflow depends on ATLAS-specific MC metadata (DSID,
   cross-section, sumOfWeights), load `atlas-opendata` and use
   `atlas_match_metadata` / `atlas_get_metadata`.

This MCP is **read-only**: it does not download files. URIs are returned
for you to hand off to `curl`, `xrdcp`, `uproot`, `coffea`, etc.

## MCP Tools Available

The `cernopendata` MCP server provides these tools (all prefixed with
`cod_`):

### Records

- `cod_get_record` — Full JSON for a record (by `recid` / `doi` / `title`)
- `cod_get_metadata` — Compact projection of the most useful fields;
  pass `field` for a single field
- `cod_resolve_record` — Resolve a DOI or exact title to a numeric `recid`

### Files

- `cod_list_files` — List data file URIs attached to a record
  (token-efficient, URIs only)
- `cod_get_file_urls` — URIs with size and checksum per file
  (for transfer planning or integrity checks)

### Directory (optional XRootD)

- `cod_list_directory` — Browse the EOSPUBLIC directory tree over XRootD.
  Requires the `[xrootd]` extra to be installed server-side; otherwise
  returns an instructive "not available" recovery message.

## MCP Resources

- `cernopendata://guide` — Overview of experiments, record types,
  collections, keywords, file-index mechanism, URI protocols.
- `cernopendata://record-fields` — Reference for the JSON fields
  returned by the Invenio record API.

## Workflow

1. If you have a DOI or exact title but no recid, call
   `cod_resolve_record` first.
2. For a compact overview of a record, use `cod_get_metadata`. Pass
   `field=` for a single value.
3. For the full record JSON (all Invenio fields), use `cod_get_record`.
4. To get file URIs for streaming or download, use `cod_list_files`
   (URIs only) or `cod_get_file_urls` (with sizes and checksums).
5. For large-campaign directory browsing where records point to
   file-indexes, use `cod_list_directory`.

## Identifiers

Provide **exactly one** of `recid` / `doi` / `title` to record and file
tools. `recid` accepts an int or a numeric string.

| Identifier | Example | Notes |
|---|---|---|
| `recid` | `1`, `12345` | Preferred; stable numeric ID. |
| `doi` | `10.7483/OPENDATA.CMS.ABCD.1234` | Full DOI string. |
| `title` | `"Higgs-to-four-lepton ..."` | Must be **exact**; no wildcards. |

## Experiments covered

- **ATLAS**, **CMS**, **LHCb**, **ALICE** — LHC detectors
- **OPERA** — earlier SPS neutrino experiment

Record types include `Dataset`, `Simulated Dataset`, `Derived Dataset`,
`Software`, `Documentation`, `Environment`, `Tool`, `Configuration`,
`Workflow`, `Supplementaries`.

## Protocols

File URIs can be returned in two protocols:

- `http` (default) — HTTPS download URL, suitable for `curl` / web
  download / most batch systems.
- `xrootd` — `root://eospublic.cern.ch//eos/...`, suitable for ROOT /
  `uproot` / `coffea` streaming.

## File indexes

Record `files` lists often contain **file-index files** rather than the
data files themselves (a `.txt` or `.json` listing the real URIs).
`cod_list_files` and `cod_get_file_urls` dereference these by default
(`expand=True`). Set `expand=False` only when you specifically want the
raw index entry.

## Recovery behaviour

All tools return error strings (never raise). When something fails the
response includes a `Recovery steps:` block naming the concrete tool to
call next — follow those suggestions instead of guessing.
