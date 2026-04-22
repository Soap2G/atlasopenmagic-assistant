---
name: rucio
description: Use the Rucio CLI to look up datasets, files, replicas, metadata, and transfer rules for authenticated ATLAS (or other VO) users. Load this skill only when the user is on lxplus or has a local Rucio client with a valid credential; do NOT load it for public ATLAS Open Data workflows (those use atlas_get_urls / cod_list_files instead). Prefer read-only commands; every write operation must be confirmed.
---

## Scope

Use this skill when the user:

- has the `rucio` command on their PATH, **and**
- has a working `rucio.cfg` plus the credential that matches its
  `auth_type` (VOMS proxy for `x509_proxy`, cached OIDC token for
  `oidc`, etc.), **and**
- is working with real experiment data (not ATLAS Open Data files).

For public ATLAS Open Data release samples, use `atlas-opendata`
(`atlas_get_urls`) or `cern-opendata` (`cod_list_files`) instead.

Do **not** invoke write operations (`rucio rule add`, `rucio did add`,
`rucio upload`, `rucio rule remove`, …) without explicit user
confirmation. Several destructive variants (`rule remove`,
`did remove`, `replica remove`, `rse remove`, `account remove`,
`erase`) are denied by default in opencode's permissions.

## Reference files

Read on demand, one level deep:

- **Authentication & credentials** — rucio.cfg search order, per-auth
  credential matrix, env vars, the prerequisite check that branches
  on `auth_type`: [reference/auth.md](reference/auth.md).
- **Full command catalogue** — every read-only and write subcommand
  with flags and legacy-to-v38 mapping: [reference/commands.md](reference/commands.md).

## Getting the CLI

On machines with the `sw.escape.eu` CVMFS mount, `rucio` is already
packaged:

```bash
export RUCIO_HOME=/cvmfs/sw.escape.eu/rucio/38.3.0
source "$RUCIO_HOME/setup-minimal.sh"
```

Pin a different version by changing the path (versions live under
`/cvmfs/sw.escape.eu/rucio/`). Off-CVMFS, `pip install rucio-clients`
works but the user is responsible for `rucio.cfg` and any VOMS/OIDC
tooling.

## Quick prereq check

```bash
command -v rucio >/dev/null 2>&1 || { echo "rucio CLI not on PATH"; exit 1; }
rucio whoami   # fails loudly if config or credential is missing
```

If `rucio whoami` fails, read `reference/auth.md` and follow the
auth-aware prerequisite block there (it branches on `auth_type`: VOMS
proxy for `x509_proxy`, nothing for `oidc`).

## CLI shape (Rucio 36+)

Rucio uses a noun-first layout: `rucio did list`, `rucio replica list
file`, `rucio rule add`. Top-level groups: `account`, `config`, `did`,
`download`, `lifetime-exception`, `opendata`, `replica`, `rse`, `rule`,
`scope`, `subscription`, `upload`. Direct commands: `whoami`, `ping`,
`test-server`. For the exhaustive list, see
[reference/commands.md](reference/commands.md). Use
`rucio <group> --help` if in doubt.

## Identifier conventions

A **DID** (Data IDentifier) is `<scope>:<name>`.

Common ATLAS scopes:

| Scope prefix | Meaning |
|---|---|
| `data15_13TeV` … `data18_13TeV` | Run 2 pp data |
| `data22_13p6TeV` … `data24_13p6TeV` | Run 3 pp data |
| `mc16_13TeV`, `mc20_13TeV`, `mc23_13p6TeV` | Monte Carlo campaigns |
| `user.<cernname>` | Per-user scope for analysis outputs |
| `group.phys-<group>` | Group-wide scope |
| `valid*` | Validation samples |

A DID can refer to a **file**, a **dataset** (a set of files), or a
**container** (a set of datasets). `rucio did show <did>` confirms
which.

## Command quick reference

Enough to cover ~90 % of read-only queries. For flags, other scopes,
or any write op, read [reference/commands.md](reference/commands.md).

| Intent | Command |
|---|---|
| Who am I? | `rucio whoami` |
| Search by pattern | `rucio did list '<scope>:<pattern>'` |
| DID type / size / status | `rucio did show <scope>:<name>` |
| Files in a dataset | `rucio did content list <scope>:<name>` |
| Metadata (xsec, filter eff) | `rucio did metadata list <scope>:<name> --plugin DID_COLUMN` |
| Where are the replicas? | `rucio replica list dataset <scope>:<name>` |
| Give me PFNs | `rucio replica list file <scope>:<name> --protocols root` |
| Who has rules on it? | `rucio rule list <scope>:<name>` |
| List RSEs | `rucio rse list` |
| Storage quota | `rucio account limit list <account>` |

Write ops needing user confirmation:

| Intent | Command |
|---|---|
| Replicate to my site | `rucio rule add <did> <n> '<rse-expr>'` |
| Pull files locally | `rucio download <did>` (consider `--nrandom 1` first) |
| Publish a user dataset | `rucio upload --scope user.<name> --rse <RSE> <files>` |

## Workflow

1. **Prereqs**: `rucio whoami`; if it fails, read `reference/auth.md`.
2. **Locate the DID**: `rucio did list '<scope>:<pattern>'`, then
   `rucio did show <scope>:<name>` to confirm type and size.
3. **Pick the follow-up** from the quick-reference table above, based
   on the user's intent.
4. **For writes**: show the exact command (including any RSE
   expression) and request explicit confirmation before running.

## Pitfalls

- **Quote** DIDs with glob characters
  (`'mc20_13TeV:*.Sherpa_*.DAOD_PHYSLITE.*'`) — the shell will
  otherwise mangle them.
- Rucio commands are **case-sensitive** on scope and name.
- `rucio did list` without `--filter type=...` can return files **and**
  containers with the same prefix.
- `rucio replica list dataset` can report incomplete replicas
  (`state=U`/`state=C`); those files aren't downloadable from that RSE.
- A container is not a dataset — `rucio did content list` on a
  container walks one level; use it recursively only when you mean to.
- `rucio download` uses `X509_USER_PROXY` when `auth_type = x509_proxy`;
  the default proxy at lxplus expires in 24 h, so long transfers can
  fail mid-way.
- DID naming differs between experiments — this skill is ATLAS-flavoured.
  CMS/LHCb scopes and datatype strings differ.

## Verification

A successful use of this skill ends with either:

- a printed DID (or list of DIDs) with confirmed type and byte size,
  and the user knowing where they can read it from; or
- a rule-id (for write operations), logged with the requesting
  account and the RSE expression used.
