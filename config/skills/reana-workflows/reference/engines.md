# REANA engine templates

One full `reana.yaml` per supported engine, taken from the upstream
`reanahub/reana-demo-root6-roofit` reference implementation. Use these
as starting points when authoring a new workflow.

## Contents
- Serial
- Snakemake
- CWL
- Yadage
- Choosing an engine

## Serial

Linear DAG, spec lives inline. **Default choice** unless the user
already has a Snakefile / CWL / Yadage graph.

```yaml
version: 0.6.0
inputs:
  files:
    - code/gendata.C
    - code/fitdata.C
  parameters:
    events: 20000
    data: results/data.root
    plot: results/plot.png
workflow:
  type: serial
  specification:
    steps:
      - name: gendata
        environment: "docker.io/reanahub/reana-env-root6:6.18.04"
        kubernetes_memory_limit: "256Mi"
        commands:
          - mkdir -p results && root -b -q 'code/gendata.C(${events},"${data}")'
      - name: fitdata
        environment: "docker.io/reanahub/reana-env-root6:6.18.04"
        kubernetes_memory_limit: "256Mi"
        commands:
          - root -b -q 'code/fitdata.C("${data}","${plot}")'
outputs:
  files:
    - results/plot.png
```

Notes:
- Each step runs as a separate Kubernetes job in sequence.
- `kubernetes_memory_limit` avoids OOM kills on data-heavy steps.
- `--filter step=gendata` on `reana-client logs` zooms into a specific
  step.

## Snakemake

Use an existing `Snakefile`. The `inputs.yaml` provides parameter
values consumed by the Snakemake config.

```yaml
version: 0.8.0
inputs:
  files:
    - code/gendata.C
    - code/fitdata.C
  directories:
    - workflow/snakemake
  parameters:
    input: workflow/snakemake/inputs.yaml
workflow:
  type: snakemake
  file: workflow/snakemake/Snakefile
outputs:
  files:
    - results/plot.png
```

The `workflow/snakemake/` directory must appear under
`inputs.directories` so the Snakefile and its helpers are staged into
the workspace. Override Snakemake's report name via
`inputs.options.report`.

## CWL

Use when portability across workflow runners matters (arvados,
toil, cwltool). `workflow.file` points to the CWL entry document.

```yaml
version: 0.6.0
inputs:
  files:
    - code/gendata.C
    - code/fitdata.C
  directories:
    - workflow/cwl
  parameters:
    input: workflow/cwl/input.yml
workflow:
  type: cwl
  file: workflow/cwl/workflow.cwl
outputs:
  files:
    - outputs/plot.png
```

The `input.yml` file mapped via `inputs.parameters.input` is the CWL
input object (not REANA's `-p` overrides — those still work and go
into `start`).

## Yadage

HEP-style packtivity DAGs. `workflow.file` points to the adage YAML.

```yaml
version: 0.6.0
inputs:
  files:
    - code/gendata.C
    - code/fitdata.C
  directories:
    - workflow/yadage
  parameters:
    events: 20000
    gendata: code/gendata.C
    fitdata: code/fitdata.C
workflow:
  type: yadage
  file: workflow/yadage/workflow.yaml
outputs:
  files:
    - fitdata/plot.png
```

Yadage parameters declared in `inputs.parameters` feed the adage
`init` stage; step-level inputs/outputs are routed by the adage spec.

## Choosing an engine

| If the user…                                   | Pick         |
|-----------------------------------------------|--------------|
| has a short, linear pipeline and no existing spec | **serial**   |
| already maintains a `Snakefile`               | **snakemake**|
| needs to run the same workflow on non-REANA CWL runners | **cwl** |
| has an existing yadage/packtivity spec (e.g. RECAST) | **yadage** |

Default to serial. Converting a serial spec to another engine later
is mechanical; picking a complex engine for a simple pipeline wastes
the user's time.
