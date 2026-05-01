# open-data-assistant-config

[![checks](https://github.com/Soap2G/lumi-assistant/actions/workflows/checks.yml/badge.svg)](https://github.com/Soap2G/lumi-assistant/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Citation: CFF](https://img.shields.io/badge/cite-CITATION.cff-blue.svg)](CITATION.cff)

A pluggable [opencode](https://opencode.ai) configuration that turns
opencode (or its CERN-flavoured sibling **Lumi**) into a **general
CERN assistant** — open data, service operations (Rucio, REANA, EOS,
CRIC, SWAN, lxbatch, …), physics analysis, detector
and MC reference, and anything else CERN-shaped that someone bothers
to write a skill for.

The repo root IS the CVMFS payload. After cloning or `rsync`ing to
CVMFS, users source `bin/setup.sh` and the assistant becomes
available from any working directory on lxplus / SWAN / any
workstation with the mount.

## Why this exists

CERN services field thousands of low-complexity tickets a year that
have well-documented answers but still consume an expert's time. A
human ticket is the most expensive way to deliver a documented answer.

This repo is the substrate for an LLM-driven assistant that absorbs
the answerable layer:

- **Service teams** (Rucio, REANA, EOS, CRIC, SWAN, lxbatch, IT-DB,
  CMSWEB, …) write a skill bundle once; the router pulls it in
  whenever a user query matches the trigger condition.
- **Analysis groups** (ATLAS, CMS, LHCb, ALICE) contribute skills
  that walk through their framework, ntuple format, or workflow.
- **Outreach and students** contribute didactic skills against the
  public open-data releases.

The router doesn't care who wrote a skill or where it lives in the
folder tree — skills resolve by their `name:` frontmatter. Drop a
`SKILL.md` into the intent bucket that matches the *user's* goal,
follow the [Skill Library Design Guide](docs/skill-design.md)
(especially **Principle 7** — the per-skill growth checklist plus
3–5 eval prompts), and it ships on the next CVMFS publish.

## How skills compose

Skills don't have to live in this repo. Three layers stack:

| Layer | Where it lives | Who writes it | When it loads |
|---|---|---|---|
| **Repo skills** | `config/skills/` here | Anyone with a merged PR | Every CVMFS user, every session |
| **Personal / draft skills** | Any dir + `OPENCODE_CONFIG_DIR` override | A service team testing locally | Only when you point `setup.sh` at it |
| **Project-local skills** | `.opencode/` in a project | Per-project authors | Only inside that project (toggle via `OPENCODE_DISABLE_PROJECT_CONFIG`) |

The contribution flow for an upstream-mergeable skill:

1. Author the `SKILL.md` against your service / framework / domain.
2. Place it under the intent category that matches the *user's* goal,
   not your tool name (Principle 1 of the design guide — yes, your
   instinct will be wrong; read the guide).
3. Add 3–5 prompts to `config/evals/cases.yaml` that should select it,
   plus 2 that should not.
4. Run `python config/evals/lint.py` from the repo root.
5. Open a PR. CI runs lint on every PR and the full skill-router eval
   on push to `main`.

If you maintain a CERN service and want to onboard your skill
backlog, see the [Validation](#validation) section for the local dev
loop and open an issue tagged `service-onboarding` to coordinate.

## Layout

The skills present today are the **seed library** — the project
deliberately starts narrow (open data) so the routing pattern is
exercised at small scale before the library expands toward the full
CERN scope (see the design guide for the eight intent categories the
library is designed to grow into).

```
open-data-assistant-config/
├── config/                        ← OPENCODE_CONFIG_DIR target
│   ├── opencode.json              ← providers (anthropic/openai/litellm), MCPs, permissions
│   ├── AGENTS.md                  ← top-level persona + critical rules
│   ├── agents/
│   │   ├── tutor.md               ← didactic, read-only
│   │   └── analysis.md            ← hands-on analysis
│   ├── evals/
│   │   ├── cases.yaml             ← prompt × expected-skill ground truth
│   │   ├── run.py                 ← skill-router eval harness (needs API key)
│   │   ├── lint.py                ← structural validator (no network)
│   │   └── README.md
│   └── skills/
│       ├── learn/                 ← atlas-notebooks, sm-analyses
│       ├── discover/              ← atlas-opendata, cern-opendata
│       ├── access/                ← physlite-basics, rucio
│       ├── compute/               ← reana, reana-workflows
│       ├── operational/           ← verification-before-completion (vendored)
│       └── infra-advisor/         ← cross-category routing
├── docs/
│   └── skill-design.md            ← Skill Library Design Guide (vendor target)
├── bin/
│   └── setup.sh                   ← sourced by users (any prefix)
├── script/
│   ├── cvmfs-deploy.sh            ← stage and optionally publish
│   ├── sync-superpowers.sh        ← rebuild vendored skills from upstream
│   └── superpowers/               ← lock + per-skill frontmatter overrides
├── .github/workflows/checks.yml   ← lint on every PR + evals on main
├── VERSION                        ← semver string; drives the staged directory name
├── LICENSE                        ← MIT
├── CITATION.cff                   ← citable artefact metadata
├── README.md
└── .gitignore
```

### Vendored skills

Some skills under `config/skills/operational/` are vendored from
upstream repos (e.g. obra/superpowers) at a pinned commit. Vendoring
beats submodules for this case because we always rewrite each skill's
`description:` to anchor it to the CERN domain — generic descriptions
out-shout our domain skills in the router (the *confusability cliff*
the design guide warns about).

The pattern: `script/superpowers/<skill>.frontmatter.md` holds our
override for one skill, and `script/sync-superpowers.sh` combines
that with the upstream body at the SHA pinned in `script/superpowers/lock`.
Run `./script/sync-superpowers.sh --check` to detect drift from the
pin; bump `sha=` and `date=` in the lock and re-run without `--check`
to update.

The upstream body changes flow through automatically; the routing-
relevant fields (`description`, `data_scope`, `name`) stay under our
control.

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

`opencode` will load providers, MCP endpoints, the top-level persona,
every sub-agent, and every skill bundle regardless of CWD.

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
  directory** — currently seeded with open-data skills, designed to
  grow into a general CERN-assistant skill library contributed by
  service teams, analysis groups, and outreach.

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

## Validation

Before opening a PR, run the structural validator from the repo root:

```bash
pip install pyyaml
python config/evals/lint.py
```

This checks frontmatter, name uniqueness, and `cases.yaml` references
without making any network calls — safe to run anywhere, including
forks. The same job runs in CI on every PR.

To run the full skill-router eval harness (sends prompts to a real
model and scores router accuracy):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
pip install pyyaml httpx
python config/evals/run.py
```

This runs in CI on push to `main`, on manual workflow dispatch, and on
PRs from the same repository (forks skip it because the secret isn't
exposed).

## Citation

If you cite or reference this configuration in academic work, internal
service documentation, or contributor write-ups, see
[`CITATION.cff`](CITATION.cff). GitHub renders a "Cite this repository"
button from that file; once a Zenodo DOI is minted, the placeholder
in `CITATION.cff` should be replaced.

## License

[MIT](LICENSE) — same as [opencode](https://github.com/sst/opencode),
[archi](https://github.com/archi-physics/archi), and the broader HEP
analysis-tools ecosystem.

## Contributing

Anything you change in `config/` ships on next `--publish`. Run
`python config/evals/lint.py` before pushing.
