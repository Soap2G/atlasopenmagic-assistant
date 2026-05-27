---
name: fts-rest
description: Use when the user runs the FTS3 REST CLI (`fts-rest-whoami`, `fts-rest-server-status`, `fts-rest-transfer-submit`, `fts-rest-transfer-list`, `fts-rest-transfer-status`, `fts-rest-transfer-cancel`, `fts-rest-delete-submit`, `fts-rest-delegate`, `fts-rest-ban`) against an FTS3 endpoint such as `https://fts3-pilot.cern.ch:8446` and needs to submit, list, inspect, or cancel point-to-point transfer jobs between SRM / XRootD / HTTPS / S3 storage endpoints, or query the user's FTS identity / server status / delegated proxy. Assumes the FTS endpoint is reachable, a valid X509 proxy (`X509_USER_PROXY`) exists, and `fts-rest-whoami -s <endpoint>` succeeds. Does NOT cover Rucio-driven transfers (Rucio uses FTS3 internally — use `rucio` for rule-based replication), FTS3 docs / configuration / installation (use `cern-docs` with `source="fts"`), or grid job submission (use PanDA / DIRAC). Disambiguator phrase: fts-rest-transfer-submit hyphenated CLI.
data_scope: internal
experiment: all
---

# fts-rest — driving the FTS3 REST CLI for cross-site transfers

The `fts-rest-*` family is the REST client for an FTS3 server. Each
binary speaks to one FTS endpoint (`-s <URL>`), submits or queries a
job, and exits — the FTS3 server then drives the actual transfers
between source and destination storage endpoints (SE) over GridFTP,
HTTPS, XRootD, or S3.

## Scope

Use this skill when the user has the `fts-rest-*` CLI on PATH and is
talking directly to an FTS3 endpoint. Typical situations:

- Submitting a one-off transfer between two SEs and checking its progress.
- Listing or filtering recently submitted jobs.
- Cancelling a stuck job.
- Verifying their FTS identity / delegated proxy.
- Submitting a delete operation against an SE.

Do **not** use this skill for:

- **Rucio-driven replication** (`rucio rule add …` enqueues transfers that
  FTS3 executes under the hood) → use the `rucio` skill. The user almost
  never needs to drop down to `fts-rest-*` for Rucio data; if they do, the
  FTS endpoint is the one configured in their RSE attributes, not one they
  pick.
- **FTS3 server / configuration / monitoring docs** ("how do I set up the
  optimizer?", "what does the OAuth2 token config look like?") → use the
  `cern-docs` skill with `source="fts"`.
- **Grid analysis job submission** (PanDA, DIRAC) — FTS3 moves files, it
  doesn't run jobs.

Write operations (`transfer-submit`, `delete-submit`, `delegate`,
`transfer-cancel`, `ban`) need explicit user confirmation. Destructive
operations (`ban` against users / hosts / SEs) are denied by default in
opencode's permissions.

## Reference files

Read on demand:

- **Authentication & endpoint setup** — X509 proxy, `X509_USER_PROXY`,
  picking the FTS endpoint, `voms-proxy-init` prerequisites, common
  pilot vs production endpoints: [reference/auth.md](reference/auth.md).
- **Full command catalogue** — every `fts-rest-*` binary, common flags,
  job-file format, JSON output examples:
  [reference/commands.md](reference/commands.md).

## Getting the CLI

The `fts-rest-*` binaries ship with the `fts-rest-client` RPM on
lxplus / CERN nodes (`/usr/bin/fts-rest-*`); off-CERN, install with
`pip install fts3` (the upstream PyPI package). On CVMFS-staged
clients the binaries are picked up from whichever Python environment
the operator deployed.

```bash
command -v fts-rest-whoami >/dev/null 2>&1 || {
  echo "fts-rest CLI not on PATH"
  exit 1
}
```

## Authentication & endpoint

FTS3 uses **X509 client certificates** (proxy). Every binary takes
`-s <endpoint>` to pick the FTS3 server. The proxy is read from
`X509_USER_PROXY` (or `/tmp/x509up_u$(id -u)` if unset).

```bash
voms-proxy-info -e -v   # confirm proxy is valid (>0 seconds left)
export FTS_ENDPOINT=https://fts3-pilot.cern.ch:8446   # pick the endpoint
fts-rest-whoami -s "$FTS_ENDPOINT"
```

Common CERN endpoints:

| Endpoint URL | Use |
|---|---|
| `https://fts3-pilot.cern.ch:8446` | Pilot / pre-prod (testing) |
| `https://fts3-public.cern.ch:8446` | CERN production for non-experiment users |
| `https://fts3-atlas.cern.ch:8446` | ATLAS production (collaboration members) |
| `https://fts3-cms.cern.ch:8446` | CMS production |
| `https://fts3-lhcb.cern.ch:8446` | LHCb production |

The right endpoint depends on the user's VO and the SEs involved.
When unsure, ask; do not guess.

See [reference/auth.md](reference/auth.md) for the auth-aware prereq
block and proxy-renewal pitfalls.

## Prereq check

```bash
command -v fts-rest-whoami >/dev/null 2>&1 || { echo "fts-rest CLI not on PATH"; exit 1; }
: "${FTS_ENDPOINT:?FTS_ENDPOINT not set (e.g. https://fts3-pilot.cern.ch:8446)}"
voms-proxy-info -e -v >/dev/null 2>&1 || { echo "no valid X509 proxy; run voms-proxy-init"; exit 1; }
fts-rest-whoami -s "$FTS_ENDPOINT"
```

If `whoami` returns anything other than the user's DN + VO, stop and
surface the error.

## Identifier conventions

A **job** has:

- **job-id** — a UUID assigned by the FTS3 server at submission
  (e.g. `4d2c…-…`). Most read-only commands take `-j <job-id>`.
- **state** — one of `SUBMITTED`, `READY`, `ACTIVE`, `FINISHED`,
  `FINISHEDDIRTY`, `FAILED`, `CANCELED`, `STAGING`, `ARCHIVING`. A
  job aggregates per-file states; the job state is the worst-case
  rollup.
- **VO**, **delegation-id**, **priority**, optional source / dest **SE**.

A **source / destination URL** is a fully-qualified SE URL, e.g.
`srm://srm-atlas.cern.ch:8443/srm/managerv2?SFN=/eos/atlas/…`,
`davs://eospublic.cern.ch:443/…`, or `root://eosatlas.cern.ch//eos/…`.

## Command quick reference

Covers ~90 % of read-only triage. For flags, output formats, and the
job-file schema, read [reference/commands.md](reference/commands.md).

| Intent | Command |
|---|---|
| Who am I at FTS? | `fts-rest-whoami -s "$FTS_ENDPOINT"` |
| Server status / queue lengths | `fts-rest-server-status -s "$FTS_ENDPOINT"` |
| My jobs (last 24 h) | `fts-rest-transfer-list -s "$FTS_ENDPOINT" -o $(whoami)` |
| Filter by state | `fts-rest-transfer-list -s "$FTS_ENDPOINT" --state ACTIVE` |
| One job's status | `fts-rest-transfer-status -s "$FTS_ENDPOINT" -j <job-id>` |
| One job's per-file detail | `fts-rest-transfer-status -s "$FTS_ENDPOINT" -j <job-id> --list-files` |

Write ops needing confirmation:

| Intent | Command |
|---|---|
| Delegate / renew proxy on the FTS server | `fts-rest-delegate -s "$FTS_ENDPOINT"` |
| Submit a transfer | `fts-rest-transfer-submit -s "$FTS_ENDPOINT" -f jobfile.json` |
| Cancel a job | `fts-rest-transfer-cancel -s "$FTS_ENDPOINT" -j <job-id>` |
| Submit a delete | `fts-rest-delete-submit -s "$FTS_ENDPOINT" -f deletefile.json` |
| Ban a user / SE (admin only, denied by default) | `fts-rest-ban -s "$FTS_ENDPOINT" …` |

## Workflow

1. **Prereqs**: proxy valid, endpoint reachable, `whoami` ok (see prereq
   block above).
2. **Read-only**: `transfer-list` to orient, then `transfer-status -j <id>`
   for one job. Use `--list-files` for per-file detail when a job is in
   `FINISHEDDIRTY` (partial failure) or `FAILED`.
3. **Submit**: build the job file (see [reference/commands.md](reference/commands.md)
   for the JSON schema) and explicitly confirm with the user before
   `transfer-submit`. The server returns the new `job-id`; record it.
4. **Cancel**: confirm with the user, then `transfer-cancel -j <id>`;
   the server may take a few seconds to flip the state.

## Pitfalls

- **Proxy lifetime.** The default VOMS proxy is valid for ~24 h; FTS
  uses a delegated copy on the server side (`fts-rest-delegate` renews
  it). A long-running transfer can outlast the local proxy without
  failing — but if you re-`whoami` mid-transfer with a stale proxy, the
  call fails. Always re-check with `voms-proxy-info -e -v`.
- **Endpoint mismatch.** Submitting an `srm://…/atlas/…` transfer to a
  CMS-flavoured FTS endpoint will be accepted but the job will fail
  authorization on the SE side. Match the FTS endpoint to the VO that
  owns the SE.
- **`FINISHEDDIRTY` is not `FAILED`.** A job with some files succeeded
  and some failed lands in `FINISHEDDIRTY`. Always `--list-files` to
  find the per-file errors; don't assume the whole transfer is dead.
- **Job files are JSON, not YAML.** Even though many examples on the
  web use indented blocks that look YAML-ish, the CLI expects strict
  JSON with `--file <path>` (`-f`).
- **`transfer-list` defaults to your own jobs only.** Querying another
  user's jobs requires VO admin rights and `-o <user>` will silently
  return your jobs if the user lacks the privilege.
- **Rucio sits on top of FTS3.** If the user is debugging a failed
  Rucio rule, the FTS-side error is often the right level to look at,
  but the *workflow* is "find the rule → find the FTS job → look at
  per-file errors". Don't drop them into `fts-rest-transfer-submit`
  directly to "fix" a Rucio replication.

## Verification

A successful use of this skill ends with either:

- a printed list of jobs / a job's state machine state plus per-file
  status if relevant; or
- a printed `job-id` (for write operations), logged with the FTS
  endpoint URL and the source / dest URLs from the job file, so the
  user can reproduce or cancel it.
