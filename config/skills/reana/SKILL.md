---
name: reana
description: Use the reana-client CLI to inspect, launch, and retrieve outputs from REANA workflows (https://reana.cern.ch or another REANA deployment). Load when the user has `reana-client` on PATH, REANA_SERVER_URL and REANA_ACCESS_TOKEN set, and asks about workflows, jobs, logs, or files on a REANA cluster.
---

## Scope

Use this skill when the user is driving a **REANA** reproducible-analysis
cluster through its CLI. REANA supports four workflow engines: Serial,
CWL, Yadage, and Snakemake. Each workflow is declared in a
`reana.yaml` at the workflow root.

Do **not** use this skill for:
- Generic Python / Jupyter execution (no REANA cluster involved).
- Pure dataset lookups — use `rucio` (authenticated) or `atlas-opendata`
  / `cern-opendata` (public) instead.
- Grid submission (HTCondor / PanDA) — REANA does its own scheduling.

Write operations (`create`, `start`, `stop`, `delete`, `upload`,
`open`) should be confirmed with the user before execution.

## Getting the CLI

On machines with the `sw.escape.eu` CVMFS mount, `reana-client` is
already packaged:

```bash
export REANA_HOME=/cvmfs/sw.escape.eu/reana/0.9.3
source "$REANA_HOME/setup-minimal.sh"

export REANA_SERVER_URL=https://reana.cern.ch
export REANA_ACCESS_TOKEN=<your-token>   # generate from the REANA UI
```

Pin a different version by changing the path (available versions are
listed under `/cvmfs/sw.escape.eu/reana/`). Outside CVMFS,
`pip install reana-client` works.

## Prerequisites (check before any action)

```bash
command -v reana-client >/dev/null 2>&1 || { echo "reana-client not on PATH"; exit 1; }
: "${REANA_SERVER_URL:?REANA_SERVER_URL not set (e.g. https://reana.cern.ch)}"
: "${REANA_ACCESS_TOKEN:?REANA_ACCESS_TOKEN not set (generate from the REANA web UI)}"
reana-client ping
```

`reana-client ping` confirms the server URL + token work together. If
it prints anything other than `OK`, stop and report the error.

### Common deployments

| URL | Purpose |
|---|---|
| `https://reana.cern.ch` | Production REANA at CERN (CERN SSO users) |
| `https://reana-qa.cern.ch` | CERN staging; may be unavailable |
| `https://reana.dev` | Upstream demo cluster |

The token is per-user and per-deployment. Users generate it from the
REANA web UI (Profile → Access Token).

## Identifier conventions

Each workflow has:
- **name** (`my-higgs-analysis`), optional `.run_number` suffix
  (`my-higgs-analysis.3`).
- **uuid** (auto-generated).
- **status**: `created` → `queued` → `running` → `finished` |
  `failed` | `stopped` | `deleted`.

Most commands accept either name-with-run-number or uuid via `-w`.

## Read-only command catalogue

### Server state
- `reana-client ping` — connectivity + auth.
- `reana-client version` — client version.
- `reana-client info` — server version, supported engines, limits.
- `reana-client quota-show` — CPU and disk usage vs quota for the
  current account.

### Workflow discovery
- `reana-client list` — all your workflows with latest status.
  Flags: `--filter status=running`, `--filter name=<substring>`,
  `--sort started`, `--page N --size M`, `--json` for scriptable output.
- `reana-client status -w <workflow>` — one workflow, with progress
  (`--include-workflow-params`, `--include-progress`,
  `--include-workspace-size`).
- `reana-client logs -w <workflow>` — full logs.
  Flags: `--filter step=<step_name>`, `--json`.
- `reana-client diff <workflow_a> <workflow_b>` — inputs / workspace
  diff between two runs.

### Workspace inspection
- `reana-client ls -w <workflow>` — list files in the workspace.
  Flags: `--filter name=<glob>`, `--filter size=+10M`, `--human-readable`.
- `reana-client du -w <workflow>` — disk usage for the workspace.
  Flags: `--summarize`, `--human-readable`, `--block-size M`.
- `reana-client download -w <workflow> <file-or-dir>` — pull outputs
  to cwd. Without a path, downloads files declared under `outputs:`
  in `reana.yaml`.

## Write operations (require confirmation)

### Workflow lifecycle
- `reana-client create -f reana.yaml -n <name>` — register a workflow.
  The `reana.yaml` declares inputs, outputs, workflow engine, and
  steps.
- `reana-client upload -w <workflow> <local-path...>` — push inputs
  into the workspace.
- `reana-client start -w <workflow>` — schedule the workflow.
  Flags: `-p <param>=<value>` to override parameters from `reana.yaml`.
- `reana-client stop -w <workflow>` — stop a running workflow.
  Irreversible.
- `reana-client delete -w <workflow>` — remove the workflow record;
  optionally `--all-runs`, `--workspace`, `--include-records`,
  `--include-workspace`.
- `reana-client mv`, `reana-client rm`, `reana-client prune` —
  workspace file edits. Confirm before deleting.

### Interactive sessions
- `reana-client open -w <workflow> jupyter` — spawn a Jupyter session
  attached to the workspace.
- `reana-client close -w <workflow>` — tear it down.

## reana.yaml at a glance

```yaml
version: 0.9.0
inputs:
  files:
    - code/analysis.py
  directories:
    - data/
  parameters:
    channel: "Zee"
workflow:
  type: serial
  specification:
    steps:
      - name: analyse
        environment: 'docker.io/rootproject/root:6.30.04-ubuntu22.04'
        commands:
          - python code/analysis.py --channel ${channel} --in data/ --out out/
outputs:
  files:
    - out/histograms.root
```

Engines differ: swap `type:` and rewrite `specification` for `cwl`,
`yadage`, or `snakemake`. CWL steps live in an external `.cwl` file;
Yadage uses adage/packtivity specs; Snakemake consumes a `Snakefile`.

## Workflow

1. Check prerequisites (`reana-client ping`, env vars).
2. `reana-client list --filter status=running` to orient.
3. For a named workflow:
   - `reana-client status -w <name> --include-progress` — is it
     running? stuck? finished?
   - `reana-client logs -w <name> --filter step=<step>` — zoom in on
     a specific step if failed.
   - `reana-client ls -w <name>` + `reana-client du -w <name>
     --summarize` — what's in the workspace.
4. For a new run:
   - Validate `reana.yaml` locally (`reana-client validate -f reana.yaml`).
   - `create` → `upload` inputs → `start` → poll `status`.
5. On success, `download` the declared outputs.

## Pitfalls

- The `<workflow>` argument is name-**and**-optional-run-number
  (`my-analysis` uses the latest run; `my-analysis.3` pins to run 3).
- `reana-client start` returns immediately; the workflow runs
  asynchronously. Poll with `status`, don't assume completion.
- `logs` output is verbose for multi-step workflows; always use
  `--filter step=<name>` when triaging a failure.
- `delete` with `--include-workspace` destroys all workspace files;
  quote `--workspace` only when that is explicitly what the user
  wants.
- `REANA_ACCESS_TOKEN` is sensitive — never print it in logs or
  suggest committing it to git.
- Quotas are per-account. `quota-show` before long runs to avoid
  mid-run termination.
- Workflow environments must be pinned by digest for reproducibility
  in production; warn if the user's `reana.yaml` uses a moving tag
  like `:latest`.

## Verification

A successful use of this skill ends with:
- for read-only intent: a printed status (one of `created`, `queued`,
  `running`, `finished`, `failed`, `stopped`, `deleted`) and, if
  applicable, the workspace listing or the relevant log excerpt.
- for write intent: a confirmed `uuid` and the command string that
  was run, so the user can reproduce or roll it back.
