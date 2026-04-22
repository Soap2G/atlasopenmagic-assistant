---
name: reana-workflows
description: Use this skill to help the user design, write, and run a REANA workflow end-to-end — authoring `reana.yaml`, choosing an engine (serial, cwl, yadage, snakemake), parameterizing steps, and executing the build-upload-start-download loop with `reana-client`. Load when the user asks how to "build a REANA workflow", "write a reana.yaml", "run my analysis on REANA", or "reproduce an analysis on reana.cern.ch". For troubleshooting an already-running workflow (status, logs), use the `reana` skill instead.
---

## Scope

Use this skill when the user is **authoring or launching** a REANA
workflow — writing a `reana.yaml` from scratch, porting an existing
analysis, or walking the full create → upload → start → download
cycle for the first time.

For inspecting an **already-running** workflow (status, logs,
workspace triage, downloads), use the `reana` skill instead. The two
skills share the auth/CLI setup; this one assumes the user can
already `reana-client ping` successfully.

Write operations (`create`, `upload`, `start`, `open`) need explicit
user confirmation. `stop`, `delete`, `rm`, `prune` are denied by
default in opencode permissions.

## Reference files (read on demand)

- **`reana.yaml` schema** — every top-level section and field:
  [reference/schema.md](reference/schema.md).
- **Engine templates** — full `reana.yaml` examples for serial, cwl,
  yadage, snakemake: [reference/engines.md](reference/engines.md).
- **End-to-end first example** — the upstream `reanahub/reana-demo-root6-roofit`
  walkthrough, verbatim: [reference/first-example.md](reference/first-example.md).

For CLI subcommand flags not covered below, see the sibling `reana`
skill's [reference/commands.md](../reana/reference/commands.md).

## Prereqs

Assume the user already has `reana-client` on PATH,
`REANA_SERVER_URL` + `REANA_ACCESS_TOKEN` exported, and `reana-client
ping` prints `OK`. If not, send them to the `reana` skill first.

On CVMFS:

```bash
source /cvmfs/sw.escape.eu/reana/0.9.3/setup-minimal.sh
```

## Anatomy of a `reana.yaml`

Every REANA workflow is declared in a single `reana.yaml` at the repo
root. Four sections matter:

```yaml
version: 0.9.0          # REANA platform version used to author this
inputs:                 # what gets staged into the workspace
  files: [...]
  directories: [...]
  parameters: {...}
workflow:               # how to run it
  type: serial | cwl | yadage | snakemake
  specification: ...    # serial only
  file: path/to/spec    # cwl | yadage | snakemake
outputs:                # what the user will download
  files: [...]
  directories: [...]
```

Optional top-level sections: `workspace.retention_days` (auto-clean
paths after N days), and engine-specific bits under
`inputs.options`. Full schema in [reference/schema.md](reference/schema.md).

### The four engines at a glance

| Engine    | `workflow.type` | Spec lives in                     | Use when                              |
|-----------|-----------------|-----------------------------------|---------------------------------------|
| Serial    | `serial`        | inline `workflow.specification`   | Linear pipelines; the 90 % default    |
| Snakemake | `snakemake`     | external `Snakefile`              | DAG with Python-flavoured rules       |
| CWL       | `cwl`           | external `workflow.cwl`           | Cross-platform portability is required|
| Yadage    | `yadage`        | external `workflow.yaml` (adage)  | HEP-style packtivity graphs           |

Pick **serial** unless the user has an existing Snakefile / CWL / Yadage
spec. For engine templates, read [reference/engines.md](reference/engines.md).

### Minimal serial template

```yaml
version: 0.9.0
inputs:
  files:
    - code/analysis.py
  parameters:
    channel: "Zee"
    nevents: 10000
workflow:
  type: serial
  specification:
    steps:
      - name: run
        environment: "docker.io/rootproject/root:6.30.04-ubuntu22.04"
        kubernetes_memory_limit: "512Mi"
        commands:
          - mkdir -p results
          - python code/analysis.py --channel ${channel} --nevents ${nevents} --out results/hist.root
outputs:
  files:
    - results/hist.root
```

Parameters declared in `inputs.parameters` are substituted as
`${name}` in commands. Override them at launch with `reana-client
start -p name=value`.

## End-to-end: build, run, download

The five canonical commands. Items marked ⚠️ need user confirmation.

```bash
# 0. validate locally before touching the server
reana-client validate -f reana.yaml

# 1. ⚠️ register the workflow
reana-client create -f reana.yaml -n <workflow-name>
export REANA_WORKON=<workflow-name>          # optional: saves typing -w

# 2. ⚠️ stage inputs (everything under inputs.files / inputs.directories)
reana-client upload

# 3. ⚠️ launch
reana-client start                           # add -p key=value to override parameters

# 4. poll
reana-client status --include-progress
reana-client logs --filter step=<step>       # only when a step fails

# 5. pull outputs once status == finished
reana-client download                        # no args = everything in outputs:
```

`reana-client create` returns immediately; `start` also returns
immediately and the workflow runs asynchronously. Always `status`
before assuming completion.

### Parameter overrides

Three layers, increasing priority:

1. defaults in `inputs.parameters` in `reana.yaml`
2. a YAML file passed via `reana-client start -f params.yaml`
3. explicit `-p key=value` flags on `start` (wins)

```bash
reana-client start -p nevents=100000 -p channel=Zmumu
```

### Re-running with tweaked inputs

```bash
# modify local files, then push a new workflow revision
reana-client upload <changed-file>
reana-client start                    # fresh run, increments .run_number
reana-client list --filter name=<workflow-name>
```

Each `start` produces a new `.run_number` suffix you can target with
`-w <name>.<n>`.

## Authoring workflow

1. **Pick the engine** (usually serial; only pick others if the user
   already has that spec).
2. **Draft `reana.yaml`** using the matching template from
   [reference/engines.md](reference/engines.md). Pin container images
   with digests (`image@sha256:...`) if the workflow is meant to be
   reproducible long-term; moving tags like `:latest` are fine for
   iteration but warn the user before a final run.
3. **`reana-client validate -f reana.yaml`** before anything else —
   catches most schema mistakes locally without consuming quota.
4. **First run small**: override `nevents` / input sizes with `-p` to
   get a minutes-scale smoke test before committing to the full job.
5. **Iterate**: edit `reana.yaml`, re-`validate`, re-`create` (with
   a new name or rely on auto-incremented run numbers), re-`start`.
6. **Download** outputs declared under `outputs.files` /
   `outputs.directories`.

## Pitfalls

- **`validate` is free, use it**. Running `create` on an invalid
  `reana.yaml` wastes a workflow slot.
- **Quota**. `reana-client quota-show` before a long job. Running out
  of CPU or disk mid-run kills the workflow.
- **Container digests**. `:latest` drifts; for anything the user wants
  to reproduce later, use `image@sha256:<digest>`.
- **Parameter substitution is textual**. `${events}` is not quoted for
  you — wrap it in `"${events}"` when the value could be a string with
  spaces or special chars.
- **`upload` with no args** uploads everything listed under `inputs.files`
  and `inputs.directories`. To push a single changed file, pass its path.
- **Workspace size**. Intermediate files stay in the workspace and count
  against your quota. Use `workspace.retention_days` to auto-clean
  temporary paths:
  ```yaml
  workspace:
    retention_days:
      tmp/*.root: 7
  ```
- **Engine file paths**. For `cwl`/`yadage`/`snakemake`, `workflow.file`
  is relative to the repo root — the file itself must also be listed
  under `inputs.directories` (or `inputs.files`) so REANA stages it
  into the workspace.
- **Secrets** never belong in `reana.yaml`. Use `reana-client secrets`
  (see `reana` skill) or pass via `-p` at `start` time.

## Verification

A successful use of this skill ends with either:
- a validated `reana.yaml` plus a **uuid** returned by `create` and a
  status printed by `reana-client status` (for launch intent); or
- a committed, reviewed `reana.yaml` that the user can run later (for
  authoring-only intent). In both cases, confirm the container images
  and parameter names before handing back.
