# reana-client command catalogue

Full list of read-only and write subcommands, plus a `reana.yaml`
template. Read this when you need a specific command, flag, or
template — SKILL.md only carries the common ones.

## Contents
- Read-only: server state, workflow discovery, workspace inspection
- Write operations: lifecycle, interactive sessions
- `reana.yaml` at a glance

## Read-only commands

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
  **Denied by default** in opencode permissions.
- `reana-client delete -w <workflow>` — remove the workflow record;
  optionally `--all-runs`, `--workspace`, `--include-records`,
  `--include-workspace`. **Denied by default.**
- `reana-client mv` — rename a workspace path. (Write, gated.)
- `reana-client rm`, `reana-client prune` — workspace file edits.
  **Denied by default.**

### Interactive sessions
- `reana-client open -w <workflow> jupyter` — spawn a Jupyter session
  attached to the workspace.
- `reana-client close -w <workflow>` — tear it down.

## `reana.yaml` at a glance

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

Reproducibility: pin container environments by digest
(`image@sha256:...`), not moving tags like `:latest`.
