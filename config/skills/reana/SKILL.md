---
name: reana
description: Use the reana-client CLI to inspect, launch, and retrieve outputs from REANA workflows (https://reana.cern.ch or another REANA deployment). Load when the user has `reana-client` on PATH, REANA_SERVER_URL and REANA_ACCESS_TOKEN set, and asks about workflows, jobs, logs, or files on a REANA cluster.
---

## Scope

Use this skill when the user is driving a **REANA** reproducible-analysis
cluster through its CLI. REANA supports four workflow engines: Serial,
CWL, Yadage, and Snakemake. Each workflow is declared in a `reana.yaml`
at the workflow root.

Do **not** use this skill for:
- Generic Python / Jupyter execution (no REANA cluster involved).
- Pure dataset lookups — use `rucio` (authenticated) or `atlas-opendata`
  / `cern-opendata` (public) instead.
- Grid submission (HTCondor / PanDA) — REANA does its own scheduling.

Write operations (`create`, `start`, `upload`, `open`, `mv`) need
explicit confirmation. Destructive ops (`stop`, `delete`, `rm`,
`prune`) are denied by default in opencode's permissions.

## Reference file

- **Full command catalogue + `reana.yaml` template**:
  [reference/commands.md](reference/commands.md). Read it when you
  need a flag, an uncommon subcommand, or the YAML schema.

## Sibling skill: authoring new workflows

For writing a `reana.yaml` from scratch, choosing an engine, and
walking the build-upload-start-download cycle for the first time, use
the **`reana-workflows`** skill. This skill (`reana`) is focused on
inspecting and triaging workflows that already exist on the server.

## Getting the CLI

On machines with the `sw.escape.eu` CVMFS mount, `reana-client` is
already packaged:

```bash
export REANA_HOME=/cvmfs/sw.escape.eu/reana/0.9.3
source "$REANA_HOME/setup-minimal.sh"
```

Pin a different version by changing the path (versions under
`/cvmfs/sw.escape.eu/reana/`). Off-CVMFS, `pip install reana-client`
works.

## Authentication

REANA has no config file. The CLI reads **two environment variables**
on every call — nothing else identifies you to the cluster.

```bash
export REANA_SERVER_URL=https://reana.cern.ch   # pick the deployment
export REANA_ACCESS_TOKEN=<your-token>          # per-user, per-deployment
```

- `REANA_SERVER_URL` — HTTPS URL of the REANA deployment.
- `REANA_ACCESS_TOKEN` — from the REANA web UI under **Profile →
  Access Token**. Tokens are bound to the deployment — a `reana.cern.ch`
  token does not work against `reana-qa.cern.ch`.

No proxy/VOMS required. Persist the exports in `~/.bashrc` or a
sourced env file; **never** commit the token to git.

Common deployments: `https://reana.cern.ch` (CERN production),
`https://reana-qa.cern.ch` (staging), `https://reana.dev` (upstream demo).

## Prereq check

```bash
command -v reana-client >/dev/null 2>&1 || { echo "reana-client not on PATH"; exit 1; }
: "${REANA_SERVER_URL:?REANA_SERVER_URL not set (e.g. https://reana.cern.ch)}"
: "${REANA_ACCESS_TOKEN:?REANA_ACCESS_TOKEN not set (generate from the REANA web UI)}"
reana-client ping
```

If `ping` prints anything other than `OK`, stop and surface the error.

## Identifier conventions

Each workflow has:
- **name** (`my-higgs-analysis`), optional `.run_number` suffix
  (`my-higgs-analysis.3` pins to run 3; no suffix = latest run).
- **uuid** (auto-generated).
- **status**: `created` → `queued` → `running` → `finished` |
  `failed` | `stopped` | `deleted`.

Most commands take either name-with-run-number or uuid via `-w`.

## Command quick reference

Enough to cover typical read-only triage. For flags and uncommon
subcommands, see [reference/commands.md](reference/commands.md).

| Intent | Command |
|---|---|
| Can I reach the server? | `reana-client ping` |
| My running workflows? | `reana-client list --filter status=running` |
| Status + progress | `reana-client status -w <wf> --include-progress` |
| Failed step logs | `reana-client logs -w <wf> --filter step=<step>` |
| Files in workspace | `reana-client ls -w <wf>` |
| Workspace size | `reana-client du -w <wf> --summarize` |
| Quota | `reana-client quota-show` |
| Validate a spec locally | `reana-client validate -f reana.yaml` |

Write ops needing confirmation:

| Intent | Command |
|---|---|
| Register a workflow | `reana-client create -f reana.yaml -n <name>` |
| Push inputs | `reana-client upload -w <wf> <paths...>` |
| Run it | `reana-client start -w <wf> [-p key=value]` |
| Pull outputs | `reana-client download -w <wf> [<path>]` |
| Interactive session | `reana-client open -w <wf> jupyter` / `close` |

## Workflow

1. Prereq check (`ping`, env vars).
2. `reana-client list --filter status=running` to orient.
3. For a named workflow:
   - `status -w <wf> --include-progress` — running? stuck? finished?
   - `logs -w <wf> --filter step=<step>` — zoom in if failed.
   - `ls -w <wf>` + `du -w <wf> --summarize` — workspace contents.
4. For a new run: `validate` → `create` → `upload` → `start` → poll
   `status` → `download` outputs on success.

## Pitfalls

- `<workflow>` is name-**and**-optional-run-number
  (`my-analysis.3` pins to run 3; `my-analysis` = latest).
- `reana-client start` returns immediately; the workflow runs
  asynchronously. Poll with `status`, don't assume completion.
- `logs` is verbose for multi-step workflows — always use
  `--filter step=<name>` when triaging a failure.
- `delete --include-workspace` destroys all workspace files. Confirm
  explicitly. (The flat `delete` is denied by default anyway.)
- `REANA_ACCESS_TOKEN` is sensitive — never print it in logs or
  suggest committing it to git.
- Quotas are per-account. `quota-show` before long runs to avoid
  mid-run termination.
- Pin container environments by digest (`image@sha256:...`) in
  production; warn if the user's `reana.yaml` uses moving tags like
  `:latest`.

## Verification

A successful use of this skill ends with:
- for read-only intent: a printed status (`created` | `queued` |
  `running` | `finished` | `failed` | `stopped` | `deleted`) and,
  if applicable, the workspace listing or the relevant log excerpt.
- for write intent: a confirmed `uuid` and the command string that
  was run, so the user can reproduce or roll it back.
