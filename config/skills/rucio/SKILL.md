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

## CLI shape (Rucio 36+)

Rucio reorganised its CLI from flat verbs (`list-dids`, `list-files`,
`add-rule`) to a noun-first, verb-second layout (`rucio did list`,
`rucio replica list file`, `rucio rule add`). Authoritative source:
https://github.com/rucio/rucio/tree/master/lib/rucio/cli. This skill
targets that layout. The legacy flat commands still exist for a
transition period under `rucio-admin`/`bin_legacy` but should not be
emitted.

Top-level groups: `account`, `config`, `did`, `download`,
`lifetime-exception`, `opendata`, `replica`, `rse`, `rule`, `scope`,
`subscription`, `upload`. Direct top-level commands: `whoami`, `ping`,
`test-server`.

Use `rucio <group> --help` and `rucio <group> <subgroup> --help` to
discover flags before invoking.

## Read-only command catalogue

### Identity and sanity
- `rucio whoami` — account, identity, e-mail on the active token.
- `rucio ping` — confirm the CLI can reach the server.
- `rucio test-server` — richer client/server connectivity check.

### Storage elements (RSEs)
- `rucio rse list` — all registered RSEs.
- `rucio rse show <RSE>` — usage, protocols, settings, attributes.
- `rucio rse attribute list <RSE>` — attributes only.
- `rucio rse distance show <SOURCE-RSE> <DEST-RSE>` — transfer distance.
- `rucio rse qos list <RSE>` — QoS policies for the RSE.

### DID discovery
- `rucio did list '<scope>:<pattern>'` — glob-style search.
  Quote the argument to stop the shell expanding `*`.
- `rucio did show <scope>:<name>` — attributes, status, parents for a
  DID (replaces legacy `stat` and `list-parent-dids`).
- `rucio did content list <scope>:<name>` — immediate children of a
  collection-type DID (files in a dataset, datasets in a container).
- `rucio did content history <scope>:<name>` — historical content of a
  collection-type DID.

### DID metadata
- `rucio did metadata list <scope>:<name>` — all metadata for one or
  more DIDs (replaces legacy `get-metadata`). Use `--plugin <name>`
  to target experiment-specific stores (ATLAS: `DID_COLUMN` for
  enriched metadata such as cross-section and filter efficiency).

### Replicas
- `rucio replica list file <scope>:<name>` — per-file PFNs. Available
  replicas only by default. Use flags like `--rses <RSE>` or
  `--protocols root` to filter (run `--help` for the full list in your
  installed version).
- `rucio replica list dataset <scope>:<name>` — per-RSE dataset
  replica summary with completeness state.

### Rules (transfer policy)
- `rucio rule list <scope>:<name>` — rules on a DID.
  Also accepts filters for account / file / subscription.
- `rucio rule show <rule_id>` — rule detail. Add `--examine` (or the
  equivalent flag reported by `--help`) for detailed transfer-error
  analysis.
- `rucio rule history <scope>:<name>` — history of rules acting on a
  DID.

### Accounts and quotas
- `rucio account list` — accounts matching a filter.
- `rucio account show <account>` — account info.
- `rucio account limit list <account>` — storage usage, quota, and
  remaining quota per RSE (replaces legacy `list-account-limits` and
  `list-account-usage`).
- `rucio account attribute list <account>` — key/value attributes.
- `rucio account identity list <account>` — auth identities.

### Scopes and subscriptions
- `rucio scope list` — existing scopes (filter by account with `--account`).
- `rucio subscription list` — subscriptions (use `--help` to confirm
  exact flags in your version).

### Replica state
- `rucio replica state list` — replicas by state (e.g. suspicious).

## Write operations (require explicit user confirmation)

### Data movement (top-level)
- `rucio download <scope>:<name>` — pull files to `./<scope>/<name>/`.
  Warn about size; suggest `--nrandom 1` for a sample. Useful flags:
  `--dir`, `--rses <RSE-expression>`, `--protocol`, `--ndownloader`,
  `--no-subdir`, `--ignore-checksum`, `--transfer-timeout`,
  `--nrandom`, `--pfn`, `--allow-tape`.
- `rucio upload --scope user.<name> --rse <RSE> <files>` — publish
  local files; confirm scope and RSE.

### DID lifecycle
- `rucio did add <scope>:<name> --type {dataset,container}` — create a
  new collection.
- `rucio did update <scope>:<name> ...` — touch, set last-accessed,
  open/close.
- `rucio did remove <scope>:<name>` — mark for expiry (deletion
  within ~24 h).
- `rucio did content add <scope>:<name> --dids <child>` — attach DIDs.
- `rucio did content remove <scope>:<name> --dids <child>` — detach.
- `rucio did metadata add/remove <scope>:<name> --key <k> --value <v>`.

### Rules
- `rucio rule add <scope>:<name> <copies> <RSE-expression>` — request
  replication. Always show the computed expression
  (e.g. `type=DATADISK&site=CERN`) before executing.
- `rucio rule remove <rule_id>` — release replicas; irreversible for
  the last rule on a dataset.
- `rucio rule update <rule_id> ...` — change expiry, lifetime, state.
- `rucio rule move <rule_id> <RSE-expression>` — create a child rule
  on a different RSE (parent is deleted once the child reaches OK).

### Replicas
- `rucio replica remove <scope>:<name>` — tombstone a replica.
- `rucio replica state update bad/unavailable/quarantine ...` — flag
  replica state problems.

### RSEs, accounts, scopes (admin-level)
- `rucio rse add/remove/update ...`, `rucio rse attribute add/remove`,
  `rucio rse protocol add/remove`, `rucio rse limit add/remove`,
  `rucio rse qos add/remove`, `rucio rse distance add/remove/update`.
- `rucio account add/remove/update`, `rucio account attribute add/remove`,
  `rucio account limit add/remove`, `rucio account identity add/remove`.
- `rucio scope add/update`.

These typically require admin privileges. Do not invoke without
confirmation and without checking the user is allowed to run them.

## Workflow

1. Verify prerequisites (`rucio whoami`, VOMS proxy).
2. If the user gave a name pattern, search with
   `rucio did list '<scope>:<pattern>'`.
3. Confirm the right DID with `rucio did show <scope>:<name>`.
4. Pick the next command based on intent:
   - "where is it" → `rucio replica list dataset <did>`
   - "give me URIs" → `rucio replica list file <did> --protocols root`
   - "what's inside" → `rucio did content list <did>`
   - "what does it know" → `rucio did metadata list <did>`
   - "who has rules on it" → `rucio rule list <did>`
   - "replicate to my site" → `rucio rule add <did> <n> <rse-expr>` (with confirmation)
   - "pull files" → `rucio download <did>` (with confirmation)

## Pitfalls

- Always **quote** DIDs containing glob characters
  (`'mc20_13TeV:mc20_13TeV.*.Sherpa_*.deriv.DAOD_PHYSLITE.*'`) — the
  shell will otherwise mangle them.
- Rucio commands are **case-sensitive** on scope and name.
- `rucio did list` without `--filter type=...` can return files AND
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
