# REANA first example: `reana-demo-root6-roofit`

Upstream "getting started" walkthrough using the canonical RooFit
demo. This is the fastest way to confirm that a user's REANA setup
works end-to-end.

Source: https://docs.reana.io/getting-started/first-example/
Repo:   https://github.com/reanahub/reana-demo-root6-roofit

## Contents
- Prereq setup
- Clone + run
- What success looks like

## Prereq setup

```bash
# 1. Install the client (skip on CVMFS)
virtualenv ~/.virtualenvs/reana
source ~/.virtualenvs/reana/bin/activate
pip install --upgrade pip
pip install reana-client

# ...or on CVMFS:
#   source /cvmfs/sw.escape.eu/reana/0.9.3/setup-minimal.sh

# 2. Point at your REANA instance
export REANA_SERVER_URL=https://reana.cern.ch
export REANA_ACCESS_TOKEN=<your-token>   # from Profile → Access Token

# 3. Sanity check
reana-client ping
```

`ping` must print `OK. Server is running.` before continuing.

## Clone and run

```bash
git clone https://github.com/reanahub/reana-demo-root6-roofit
cd reana-demo-root6-roofit

# Register a new workflow named "roofit"
reana-client create -w roofit
export REANA_WORKON=roofit       # so you don't need -w on every call

# Stage inputs (everything under inputs.files in reana.yaml)
reana-client upload

# Launch
reana-client start

# Poll until finished
reana-client status
reana-client logs                # add --filter step=gendata / fitdata to zoom in

# Inspect the workspace
reana-client ls

# Download the one declared output
reana-client download results/plot.png
```

## What success looks like

- `reana-client status` eventually prints `finished`.
- `results/plot.png` appears in cwd after `download`.
- The run has two steps: `gendata` (generates a synthetic dataset)
  and `fitdata` (fits it and writes the PNG).

If `status` reports `failed`, the most useful next command is:

```bash
reana-client logs --filter step=<name-of-failing-step>
```

## What to copy from this example into a new workflow

- The `inputs.files` + `inputs.parameters` layout: put code under
  `code/` and declare it in `inputs.files`; put runtime knobs in
  `inputs.parameters`.
- The `mkdir -p results && …` pattern in the first step, so the
  output directory exists before downstream steps write to it.
- `kubernetes_memory_limit` per step, tuned to what the step
  actually needs. Start at `256Mi`, raise if the job OOM-kills.
- The discipline of declaring `outputs.files` explicitly so the user
  can `reana-client download` with no arguments.
