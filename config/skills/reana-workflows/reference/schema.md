# `reana.yaml` schema reference

Full field-level reference for the `reana.yaml` specification. Upstream
docs: https://docs.reana.io/reference/reana-yaml/

## Contents
- Top-level sections
- `inputs` (files, directories, parameters, options)
- `workflow` (type, specification, file, resources)
- `outputs` (files, directories)
- `workspace` (retention_days)
- Engine-specific `inputs.options`

## Top-level sections

| Key         | Required | Purpose                                              |
|-------------|----------|------------------------------------------------------|
| `version`   | optional | REANA platform version used to author, e.g. `0.9.0`  |
| `inputs`    | optional | What gets staged into the workspace before the run   |
| `workflow`  | **required** | How to run: engine type + spec                   |
| `outputs`   | optional | What `reana-client download` (no args) pulls back    |
| `workspace` | optional | Storage policies (retention, quota hints)            |
| `tests`     | optional | Upstream test features — not user-facing             |

## `inputs`

```yaml
inputs:
  files:
    - code/analysis.py
    - code/utils.py
  directories:
    - workflow/snakemake
    - data/
  parameters:
    channel: "Zee"
    nevents: 10000
  options:
    CACHE: "off"          # serial-only
```

- **`files`** — individual paths transferred into the workspace before
  the run.
- **`directories`** — transferred recursively. Use this for engine
  spec trees (`workflow/snakemake/`, `workflow/cwl/`).
- **`parameters`** — name/value pairs substituted as `${name}` in
  commands. Override at launch with `reana-client start -p name=value`
  or `-f params.yaml`.
- **`options`** — engine-specific operational flags (see table below).

### Engine-specific `inputs.options`

| Property    | Engine     | Purpose                                               |
|-------------|------------|-------------------------------------------------------|
| `CACHE`     | serial     | Enable/disable step result caching (`on` / `off`)     |
| `FROM`      | serial     | Partial execution: start from step name               |
| `TARGET`    | serial, cwl| Partial execution: stop at step name                  |
| `toplevel`  | yadage     | Working directory or remote repo source               |
| `initdir`   | yadage     | Initial directory for local workflows                 |
| `initfiles` | yadage     | YAML files with initial parameters                    |
| `report`    | snakemake  | Custom report filename (default: `report.html`)       |

## `workflow`

```yaml
workflow:
  type: serial | cwl | yadage | snakemake     # required
  # exactly one of the two below:
  specification: {...}                         # serial: inline steps
  file: workflow/<spec>.<ext>                  # cwl | yadage | snakemake
  resources:                                   # optional
    cvmfs:
      - atlas.cern.ch
    kerberos: true
```

- **`type`** — selects the engine. The rest of the `workflow` block
  depends on it.
- **`specification`** (serial only) — inline DAG, see below.
- **`file`** (cwl/yadage/snakemake) — path to the external spec,
  relative to the repo root. The spec directory must also appear
  under `inputs.directories` so REANA can stage it.
- **`resources`** — attach extra capabilities: CVMFS repos, Kerberos,
  Rucio secrets, voms-proxy, compute backends.

### Serial `workflow.specification`

```yaml
workflow:
  type: serial
  specification:
    steps:
      - name: gendata
        environment: "docker.io/reanahub/reana-env-root6:6.18.04"
        kubernetes_memory_limit: "256Mi"
        commands:
          - mkdir -p results
          - root -b -q 'code/gendata.C(${events},"${data}")'
      - name: fitdata
        environment: "docker.io/reanahub/reana-env-root6:6.18.04"
        kubernetes_memory_limit: "256Mi"
        commands:
          - root -b -q 'code/fitdata.C("${data}","${plot}")'
```

Each `step`:
- `name` (optional) — used in log filters (`logs --filter step=<name>`).
- `environment` (**required**) — container image URI. Digest-pinned
  in production.
- `commands` (**required**) — list of shell commands; each runs as a
  separate job in sequence.
- `kubernetes_memory_limit`, `kubernetes_job_timeout`,
  `compute_backend`, `kerberos`, `voms_proxy`, `rucio` — optional
  per-step resource hints.

## `outputs`

```yaml
outputs:
  files:
    - results/plot.png
  directories:
    - results/
```

`reana-client download` with no arguments pulls everything under
`outputs.files` + `outputs.directories`.

## `workspace`

```yaml
workspace:
  retention_days:
    tmp/*.root: 7
    logs/*: 30
```

Per-glob auto-expiry. Reduces quota pressure on iterative runs.

## Parameterization

Inside `commands`, reference input parameters as `${name}`:

```yaml
parameters:
  events: 20000
  data: results/data.root
---
commands:
  - root -b -q 'code/gendata.C(${events},"${data}")'
```

Substitution is **textual** — quote the template when the value might
contain spaces or special chars.

Override at launch:

```bash
# single param
reana-client start -p events=100000

# multiple
reana-client start -p events=100000 -p data=results/big.root

# or from a YAML file
reana-client start -f params.yaml
```

Priority (highest wins): `-p` flags > `-f` file > defaults in `reana.yaml`.
