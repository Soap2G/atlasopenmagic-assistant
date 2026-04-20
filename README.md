# open-data-assistant-config

Standalone [opencode](https://opencode.ai) configuration for the
**ATLAS Open Data assistant**, packaged for direct CVMFS deployment.

The repo root IS the CVMFS payload. After cloning or `rsync`ing to
CVMFS, users source `bin/setup.sh` and the assistant becomes available
from any working directory.

## Layout

```
open-data-assistant-config/
├── config/                        ← OPENCODE_CONFIG_DIR target
│   ├── opencode.json              ← providers (anthropic/openai/litellm), MCPs, permissions
│   ├── AGENTS.md                  ← top-level persona
│   ├── agents/
│   │   ├── tutor.md               ← didactic, read-only
│   │   └── analysis.md            ← hands-on analysis
│   └── skills/
│       ├── atlas-opendata/        ← atlasopenmagic MCP wrapper
│       ├── cern-opendata/         ← cernopendata MCP wrapper
│       ├── atlas-notebooks/       ← outreach notebook index
│       ├── physlite-basics/       ← DAOD_PHYSLITE + uproot primer
│       └── sm-analyses/           ← 7 SM walkthroughs
├── bin/
│   └── setup.sh                   ← sourced by users (any prefix)
├── script/
│   └── cvmfs-deploy.sh            ← stage and optionally publish
├── VERSION                        ← semver string; drives the staged directory name
├── README.md
└── .gitignore
```

## Local dev

Clone, then source the setup script. It picks up its own location — no
path baking needed.

```bash
git clone <this repo> open-data-assistant-config
cd open-data-assistant-config
source bin/setup.sh
# -> exports OPENCODE_CONFIG_DIR=$(pwd)/config
# -> exports OPENCODE_DISABLE_PROJECT_CONFIG=1

export ANTHROPIC_API_KEY=sk-ant-...
opencode    # or `lumi` if using the CVMFS-deployed binary
```

`opencode` will load providers, MCP endpoints, the ATLAS Open Data
persona, the two sub-agents, and the five skills regardless of CWD.

To layer a local project `.opencode/` on top (override certain
settings per-project), comment out the `OPENCODE_DISABLE_PROJECT_CONFIG`
export in `bin/setup.sh`.

## Deploying to CVMFS

`script/cvmfs-deploy.sh` does not hard-code any CVMFS repository or
path — pass them on the command line. It has two modes: stage-only
(default) and publish.

### Stage only (default, safe to run anywhere)

```bash
./script/cvmfs-deploy.sh
```

Produces `dist/cvmfs-stage/<VERSION>/` plus a
`dist/cvmfs-stage/latest` symlink. Inspect the staged tree before
publishing.

### Publish to CVMFS

Run this on a CVMFS publisher node (must have `cvmfs_server` in PATH
and write access to the target CVMFS repository):

```bash
./script/cvmfs-deploy.sh \
    --cvmfs-base /cvmfs/sw.escape.eu/open-data-assistant \
    --cvmfs-repo sw.escape.eu \
    --publish
```

What happens:

1. `cvmfs_server transaction sw.escape.eu`
2. `rsync -a --delete dist/cvmfs-stage/ /cvmfs/sw.escape.eu/open-data-assistant/`
3. `cvmfs_server publish sw.escape.eu`

Users on any lxplus / SWAN / workstation with the CVMFS mount then do:

```bash
source /cvmfs/sw.escape.eu/open-data-assistant/latest/bin/setup.sh
lumi    # or opencode
```

The `latest` symlink tracks whichever version was last published.
Explicit version pinning: `/cvmfs/.../<VERSION>/bin/setup.sh`.

### Bumping the version

1. Edit `VERSION` (bump the semver).
2. Commit.
3. Re-run `./script/cvmfs-deploy.sh --publish ...`. Old versions on
   CVMFS remain, since `rsync --delete` only deletes what is no longer
   under `dist/cvmfs-stage/` (which is a full tree including previous
   versions if you staged them).

> **Note**: to keep older versions on CVMFS while publishing a new one,
> either stage multiple versions before publishing, or publish to a
> per-version subdirectory. The included script publishes the full
> stage tree as-is.

## Relationship with Lumi

This repo is a sibling of Lumi:

- **Lumi** (`/cvmfs/sw.escape.eu/lumi/`) ships the opencode **binary**
  and a CERN-developer config (LiteLLM, Rucio/EOS permissions).
- **open-data-assistant-config** (this repo) ships **only a config
  directory**, aimed at ATLAS Open Data users with Binder / Colab /
  SWAN / local workflows.

They coexist: the Lumi binary is perfectly capable of loading this
repo's config. Once both are on CVMFS:

```bash
source /cvmfs/sw.escape.eu/lumi/latest/bin/setup.sh               # get the `lumi` binary
source /cvmfs/sw.escape.eu/open-data-assistant/latest/bin/setup.sh # point it at this config
lumi
```

The order matters only if both export conflicting variables — the
last `source` wins. `setup.sh` here sets `OPENCODE_CONFIG_DIR`, which
is loaded *after* the Lumi `OPENCODE_CONFIG` file by opencode's config
loader ([config.ts:1317-1352](https://github.com/opencode-ai/opencode/blob/dev/packages/opencode/src/config/config.ts)),
so this config wins on overlap.

## Contributing

See the sibling repo `open-data-assistant` for a longer-form
contributors' guide (how to author a SKILL.md, add a sub-agent, etc.).
Anything you change in `config/` ships on next `--publish`.
