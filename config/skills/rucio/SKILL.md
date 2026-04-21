---
name: rucio
description: Use the Rucio CLI to look up datasets, files, replicas, metadata, and transfer rules for authenticated ATLAS (or other VO) users. Load this skill only when the user is on lxplus or has a local Rucio client with a valid VOMS proxy; do NOT load it for public ATLAS Open Data workflows (those use atlas_get_urls / cod_list_files instead). Prefer read-only commands; every write operation must be confirmed.
---

## Scope

Use this skill when the user:

- has the `rucio` command on their PATH, **and**
- has a valid VOMS proxy (`voms-proxy-info -actor`), **and**
- is working with real experiment data (not ATLAS Open Data files).

For public ATLAS Open Data release samples, use `atlas-opendata`
(`atlas_get_urls`) or `cern-opendata` (`cod_list_files`) instead —
those return public HTTPS / XRootD URIs that do not require Rucio.

Do **not** invoke write operations (`add-rule`, `add-dataset`,
`upload`, `delete-rule`, `erase`) without explicit user confirmation.
Data management actions can trigger replication across sites and are
often irreversible.

## Getting the CLI

On machines with the `sw.escape.eu` CVMFS mount, `rucio` is already
packaged — users don't need to install anything:

```bash
export RUCIO_HOME=/cvmfs/sw.escape.eu/rucio/38.3.0
source "$RUCIO_HOME/setup-minimal.sh"
```

Pin a different version by changing the path (available versions are
listed under `/cvmfs/sw.escape.eu/rucio/`). Outside CVMFS, `pip
install rucio-clients` works but users are responsible for the VOMS
proxy tooling.

## Prerequisites (check before any action)

Run these once at the start of a session and bail out with an
instructive error if they fail.

```bash
command -v rucio >/dev/null 2>&1 || { echo "rucio CLI not on PATH"; exit 1; }
voms-proxy-info -exists -valid 0:30 >/dev/null 2>&1 || {
  echo "No valid VOMS proxy. Run: voms-proxy-init -voms atlas"; exit 1;
}
rucio whoami
```

`rucio whoami` returns the account, identity, and e-mail; use it to
confirm the right identity before any query.

Required environment:

- `RUCIO_ACCOUNT` — the Rucio account to act as (often the CERN
  username for ATLAS users; can also be a group account).
- `X509_USER_PROXY` — path to the VOMS proxy. Normally set
  automatically by `voms-proxy-init`.

## Identifier conventions

A **DID** (Data IDentifier) is `<scope>:<name>`.

Common ATLAS scopes:

| Scope prefix | Meaning |
|---|---|
| `data15_13TeV`, `data16_13TeV`, `data17_13TeV`, `data18_13TeV` | Run 2 pp data |
| `data22_13p6TeV`, `data23_13p6TeV`, `data24_13p6TeV` | Run 3 pp data |
| `mc16_13TeV`, `mc20_13TeV`, `mc23_13p6TeV` | Monte Carlo campaigns |
| `user.<cernname>` | Per-user scope for analysis outputs |
| `group.phys-<group>` | Group-wide scope |
| `valid*` | Validation samples |

A DID can refer to a **file**, a **dataset** (a set of files), or a
**container** (a set of datasets). `rucio list-dids` shows which.

## Read-only command catalogue

### Identity and sanity
- `rucio whoami` — account, identity, e-mail.
- `rucio ping` — confirm the CLI can reach the server.
- `rucio list-rses` — list all Rucio Storage Elements.
- `rucio list-rse-attributes <RSE>` — attributes of one RSE.

### Dataset and file discovery
- `rucio list-dids '<scope>:<pattern>'` — glob-style search. Quote the
  argument to stop the shell expanding `*`.
  Flags: `--filter type=<container|dataset|file>`, `--short` (names only).
- `rucio list-dids --recursive '<scope>:<container>'` — walk children.
- `rucio list-files <scope>:<name>` — files in a dataset/container,
  with size and checksum.
- `rucio list-content <scope>:<name>` — immediate children only
  (files for a dataset, datasets for a container).
- `rucio list-parent-dids <scope>:<name>` — which containers/datasets
  contain this DID.

### Metadata
- `rucio get-metadata <scope>:<name>` — generic metadata
  (bytes, events, GUID, deterministic flag, datatype).
- `rucio get-metadata --plugin DID_COLUMN <scope>:<name>` — ATLAS-only
  enriched metadata (cross-section, filter eff, generator tune).
- `rucio stat <scope>:<name>` — compact summary (type, bytes, events).

### Replicas
- `rucio list-dataset-replicas <scope>:<name>` — per-RSE counts and
  completeness (`state=A` means "available").
- `rucio list-file-replicas <scope>:<name>` — per-file URIs.
  Add `--protocols root` or `--protocols https` to choose a protocol.
- `rucio list-file-replicas --rse <RSE> <scope>:<name>` — pin to one RSE.

### Rules (transfer policy)
- `rucio list-rules --account <account>` — your transfer rules.
- `rucio list-rules <scope>:<name>` — rules on a given DID.
- `rucio rule-info <rule_id>` — detail for one rule.

### Usage
- `rucio list-account-limits <account>` — quota per RSE.
- `rucio list-account-usage <account>` — used space per RSE.

## Write operations (require explicit user confirmation)

- `rucio add-rule <scope>:<name> <copies> <RSE-expression>`
  — request replication. Always show the user the computed expression
  (e.g. `type=DATADISK&site=CERN`) before executing.
- `rucio download <scope>:<name>` — pull files to `./<scope>/<name>/`.
  Warn about size; suggest `--nrandom 1` for a sample.
- `rucio upload --scope user.<name> --rse <RSE> <files>` — publish
  local files; confirm scope and RSE.
- `rucio delete-rule <rule_id>` — release replicas. Irreversible
  for the last rule on a dataset.

## Workflow

1. Verify prerequisites (`whoami`, proxy).
2. If the user gave a name pattern, search with
   `rucio list-dids '<scope>:<pattern>' --short`.
3. Confirm the right DID with `rucio stat <scope>:<name>` (type and
   size).
4. Pick the next command based on intent:
   - "where is it" → `list-dataset-replicas`
   - "give me URIs" → `list-file-replicas --protocols root`
   - "what's inside" → `list-files` or `list-content`
   - "what does it know" → `get-metadata`
   - "replicate to my site" → `add-rule` (with confirmation)
   - "pull files" → `download` (with confirmation)

## Pitfalls

- Always **quote** DIDs containing glob characters
  (`'mc20_13TeV:mc20_13TeV.*.Sherpa_*.deriv.DAOD_PHYSLITE.*'`) — the
  shell will otherwise mangle them.
- Rucio commands are **case-sensitive** on scope and name.
- `list-dids` without `--filter type=...` can return files AND
  containers with the same prefix; filter to what you want.
- `list-dataset-replicas` can report incomplete replicas
  (`state=U`/`state=C`); these files are not downloadable from that
  RSE.
- A container is not a dataset — `list-files` on a container walks
  recursively and can return millions of entries; use `--short` and
  consider `wc -l`.
- `rucio download` uses the local `X509_USER_PROXY`; at lxplus the
  default proxy expires in 24 h, so long transfers can fail mid-way.
- DID naming differs between experiments — this catalogue is
  ATLAS-specific. CMS/LHCb scopes and datatype strings differ.

## Verification

A successful use of this skill ends with either:
- a printed DID (or list of DIDs) with confirmed type and byte size,
  and the user knowing where they can access it from; or
- a rule-id (for write operations), logged with the requesting
  account and the RSE expression used.
