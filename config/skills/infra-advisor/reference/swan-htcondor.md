# SWAN + HTCondor — interactive-plus-batch digest

Distilled from the upstream SWAN-HTCondor integration docs. Read this
when the user wants to **develop in a notebook but scale out to the
CERN batch farm** without switching tools.

- Canonical source: https://swan.docs.cern.ch/condor/intro/
- Sibling pages (one level each):
  - configure_session/, create_cluster/, create_client/
  - execute_and_monitor/, inspect_results/, resume_work/, move_to_batch/
- Last refreshed against upstream: 2026-04-24

If the user hits a Dask / dask-labextension specific issue that this
digest doesn't cover, WebFetch the relevant sibling page above.

## What the integration is

SWAN ships a Dask-over-HTCondor adaptor (`SwanHTCondorCluster`) plus
the Dask JupyterLab extension. The effect:

- **Same notebook** drives interactive exploration on the SWAN session
  **and** a cluster of HTCondor worker pods on the CERN batch farm.
- Frameworks on top (RDataFrame distributed, coffea) rely on Dask, so
  the same analysis code scales from 1 node → N nodes with a client
  swap.
- When an analysis stabilises, the same HTCondor submission can be
  driven from the command line (`condor_submit`) as a pure batch job.

This is the **interactive-to-batch ramp** the upstream docs advertise
— one codebase, three execution shapes (single-node, Dask-distributed,
pure batch).

## Enable it

1. Open https://swan.cern.ch.
2. In the session config form:
   - **Platform**: `AlmaLinux9` (required for JupyterLab extension).
   - **Software stack**: default (tracks latest LCG / coffea /
     RDataFrame), unless the user needs a pinned older version.
   - Tick the option that enables **HTCondor pool at CERN**.
3. Start the session. The Dask JupyterLab extension loads a sidebar
   panel that creates and manages a `SwanHTCondorCluster` graphically
   — no Python required to spawn the cluster.

## Typical notebook idiom (programmatic)

The extension can also be driven from Python. The minimum pattern
looks like:

```python
from dask_lxplus import SwanHTCondorCluster   # swan's dask-htcondor
from dask.distributed import Client

cluster = SwanHTCondorCluster()          # declare the pool
cluster.scale(10)                        # ask for 10 worker jobs
client = Client(cluster)                 # connect
print(client)                            # dashboard URL + workers
```

After that, any Dask-aware computation (`dask.array`, `dask.dataframe`,
`RDataFrame` with Dask backend, `coffea.processor` with Dask
executor) runs on the HTCondor workers.

> The exact class name and import path can drift — check
> `swan.docs.cern.ch/condor/create_cluster/` for the current form if
> the snippet above fails.

## Move from interactive to batch

When the analysis is stable:

1. Dump the notebook to a `.py` file (or keep a driver script).
2. Write a classical `condor_submit` file pointing at the script and
   requesting the same resources the Dask cluster used.
3. Submit on lxplus with `condor_submit`; the script runs without a
   SWAN session.

This path is explicitly documented upstream (`condor/move_to_batch/`).
The advisor should name it as *"same code, run twice: once via Dask
from the notebook, once as a pure condor job"*.

## Where it integrates

- **Data**: the HTCondor workers inherit SWAN's CVMFS/EOS view — Open
  Data URIs (`root://eospublic.cern.ch/…`) work unchanged; Rucio-staged
  files on EOS work too.
- **Frameworks that know about Dask**: distributed RDataFrame,
  coffea, dask-awkward. See `columnar-frameworks.md`.
- **Successor**: when the user wants pinned, paper-grade reproducibility,
  wrap the same entry script in a `reana.yaml` (serial step that calls
  the script). SWAN is for iteration; REANA is for preservation.

## Routing heuristic for the advisor

| User's goal                                          | Answer                                          |
|------------------------------------------------------|-------------------------------------------------|
| "I want to scale my notebook analysis across nodes"  | SWAN + HTCondor integration (Dask client)       |
| "I've stabilised the code, run it nightly in batch"  | Same script via `condor_submit` on lxplus       |
| "Reproducible run for a paper"                       | Wrap the batch command in a REANA serial step   |
| "I need GPUs"                                        | See `cern-gpus.md` — SWAN T4 or ml.cern.ch      |

## Pitfalls

- **Start small**. `cluster.scale(N)` with a large N without limits
  will happily starve your fair-share on the farm. Start at 2–4
  workers and raise only after confirming the job shape.
- **Quota != immediate**. HTCondor provisions workers asynchronously
  — `client.wait_for_workers(n)` before computing if you care about
  having the full fleet.
- **Version drift**. The `dask-lxplus` / `SwanHTCondorCluster` API
  has churned. If an import or class name fails, re-check
  `swan.docs.cern.ch/condor/` rather than guessing.
- **Not for GPUs**. The integration is CPU-only by default. GPU paths
  live elsewhere (`cern-gpus.md`).
