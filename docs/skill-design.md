# Skill Library Design Guide — CERN Assistant

> This is the version that ships with the code, gets versioned
> with the skills it governs, and is covered by the repo's Zenodo DOI
> when minted. If you edit one side, sync the other — but the in-repo
> copy is authoritative for any reference cited from `config/`.

> A reference for humans contributing skills, and for Agents when reasoning about which skill to invoke. Read before adding, renaming, or restructuring anything under `config/skills/`.

## Purpose & scope

This document governs the organization of an opencode-based assistant whose initial scope is ATLAS Open Data, but whose intended trajectory expands toward a general **CERN assistant** covering:

- Open data tooling (atlasopenmagic, cernopendata, outreach notebooks)
- Operational infrastructure (Rucio, REANA, DIRAC, PanDA, CRIC, EOS, CVMFS)
- Real analysis frameworks (Athena, EventLoop, AnalysisBase, TopCPToolkit, EasyJet)
- Statistical tooling (pyhf, HistFitter, RooFit, combinations)
- Physics & detector reference (DAOD formats, subsystems, MC generators, calibrations)
- User-side workflow (LCG/View setup, Git, CI for physics code)

Realistic end-state library size: **several hundred skills**, with high internal semantic density (HEP acronyms, parallel toolchains, near-synonym verbs across infrastructures).

## The failure mode this guide is designed to prevent

Li (2026, [arXiv:2601.04748](https://arxiv.org/abs/2601.04748)) shows that as a flat skill library grows, selection accuracy stays stable up to a critical size, then **drops sharply** — a phase transition, not a gradual decline. The dominant cause is not library size in the abstract; it is **semantic confusability** between skill descriptions. The proposed mitigation is hierarchical organization: route into a category first, then disambiguate within it.

For our domain, two properties make the cliff arrive earlier than the paper's generic curves suggest:

1. **Acronym density.** DAOD/AOD/ESD/RAW/PHYSLITE/PHYS/NanoAOD/MiniAOD all live in the same semantic neighborhood.
2. **Parallel verbs across infrastructures.** Rucio *downloads*, REANA *fetches*, DIRAC *stages*, EOS *copies*. Naive descriptions collide.

The whole design below exists to keep us off the cliff while the library grows ~50×.

---

## Principle 0: descriptions, not bodies, are the interface

The router selects skills by reading their `description` field, not their content. Two skills with overlapping descriptions but unrelated bodies will collide. Two skills with near-identical bodies but surgically distinct descriptions will not. **Description writing is the highest-leverage activity in this repo.**

Every description must answer three questions in its first two sentences:

1. **Trigger** — what user-side situation activates this skill ("user has a DSID and wants URLs", not "ATLAS data tools")
2. **Scope boundary** — what is explicitly *not* covered, especially neighbors
3. **Disambiguator** — at least one phrase that appears in this description and nowhere else in the library

**Bad:** *"Tools for working with ATLAS Open Data datasets."*
**Good:** *"Use when the user has an ATLAS Open Data DSID or process name and needs file URLs, cross-sections, or sum-of-weights for the 2024 release. Does not cover internal/collaboration datasets (see `discover/rucio-find-datasets`) or non-ATLAS data."*

---

## Principle 1: categorize by user intent, tag by tool

The HEP-native instinct is to organize by tool: `rucio/`, `reana/`, `athena/`. **Resist this.** Tools cluster on the same workflow stages, and the router will struggle to disambiguate "I want to find data" between Rucio, CRIC, and atlasopenmagic when each has its own folder.

Organize by **what the user is trying to do**, and let the tool name live in filenames or frontmatter.

### Recommended top-level structure

```
config/skills/
├── discover/      # finding things — datasets, samples, runs, MC processes, conditions
├── access/        # getting bytes local — staging, mounting, streaming, replication
├── compute/       # running jobs — grid submission, REANA workflows, batch
├── analyze/       # operating on events — frameworks, ntuples, histogramming
├── interpret/     # statistics & combinations — pyhf, fits, limits, systematics
├── reference/     # what-things-are — DAOD formats, subsystems, MC generators
├── operational/   # ops & sysadmin — monitoring jobs, troubleshooting infra
└── learn/         # tutorials & worked examples — read-only didactic content
```

These eight are chosen because:

- They are **mutually exclusive in the user's head**. "I want to find data" feels different from "I want to run a job", in a way that "Rucio" and "DIRAC" do not.
- They are **stable across experiments** — ATLAS, CMS, LHCb users all do roughly these eight things.
- They map cleanly to **permission tiers** (`learn` is read-only; `operational` and `compute` need progressively higher trust).
- A single user query usually sits in **one** category at a time, which is what the router needs.

Same tool, multiple categories — no ambiguity:

```
discover/rucio-list-datasets.md
access/rucio-download.md
compute/rucio-rule-create.md
operational/rucio-troubleshoot-stuck-rule.md
```

Eight is at the upper end of comfortable top-level fan-out. If you find yourself wanting a ninth, first try to merge.

---

## Principle 2: introduce sub-hierarchy lazily, not eagerly

A flat ~10-skill category routes fine. Past that, introduce a **category-level router skill** that lists sub-skills with one-line summaries — this gives the router the two-step selection that the paper's hierarchical-routing experiments rely on.

**Trigger to nest:**

- More than ~12 skills in a single category, OR
- Two or more skills in the category share 3+ key terms in their descriptions

**Do not pre-build empty hierarchy levels.** Empty branches confuse the router as much as overcrowded siblings. Hierarchy is a response to density, not a default.

When you do nest, the natural second axis inside an intent category is usually **infrastructure / experiment**:

```
analyze/
├── ROUTER.md                 # "for ATLAS Athena → see athena/, for…"
├── athena/
│   ├── eventloop-skeleton.md
│   ├── athanalysis-config.md
│   └── …
├── coffea/
├── uproot-rdataframe/
└── opendata-walkthroughs/
```

---

## Principle 3: sub-agents are the second routing layer

opencode supports sub-agents (`tutor`, `analysis` today). These are the natural enforcement point for two things skill-level routing cannot do:

1. **Permission scoping** — `tutor` reads only; `analysis` runs code; a future `operational` agent would touch grid jobs; a future `internal-analysis` agent would access non-public Rucio scopes.
2. **Persona / context** — system prompt, default conventions, citation style, expected technical level.

### Scaling path

| Library size | Sub-agents | Notes |
|---|---|---|
| 9–30 | 2 (`tutor`, `analysis`) | Current setup. Adequate. |
| 30–100 | 3–5 | Each agent owns 1–3 top-level intent categories. |
| 100–300 | 4–6 + spawnable specialists | Some agents become invokable on demand rather than always-loaded. |
| 300+ | Reconsider | Past 6 always-loaded agents the routing problem just migrates up a level. |

A defensible 5-agent split for the full CERN scope:

- `tutor` — read-only, owns `learn/` + `reference/`
- `analyst` — hands-on, owns `analyze/` + `interpret/`
- `data-wrangler` — owns `discover/` + `access/`
- `compute-runner` — owns `compute/`, requires explicit user confirmation for submissions
- `ops` — owns `operational/`, gated, never auto-invoked

Avoid going past 5–6. The paper's whole point is that compiling agents into skills wins; we use sub-agents only where they're load-bearing for permissions or persona.

---

## Principle 4: skill description writing rules

For every skill, the description field must follow these rules. They are not stylistic — they are the mechanical cause of whether the router gets it right.

1. **Lead with the trigger condition, not the topic.** "Use when the user has X and wants Y" beats "Tools for X."
2. **State what is out of scope**, especially the closest neighbor skill by name.
3. **Use the most specific term in your domain.** "DAOD_PHYSLITE" not "ATLAS format". "Rucio replication rule" not "Rucio operation".
4. **Include one disambiguator phrase** that appears in this description and nowhere else in the library. Grep it before merging.
5. **Avoid generic verbs.** "Helps with", "supports", "for working with" carry no routing signal.
6. **No marketing language.** "Powerful", "comprehensive", "robust" are noise to the router.
7. **One skill = one user task.** If the description needs "or" to capture what the skill does, split it.
8. **Spell out acronyms on first use** in the description, even if the skill body assumes them. The router doesn't read the body.

---

## Principle 5: CERN/HEP-specific anti-patterns

These are failure modes that aren't in the generic literature but bite hard in this domain.

- **Acronym shadowing.** "AOD" alone is ambiguous (which experiment? which generation?). Always qualify: "ATLAS xAOD", "CMS NanoAOD".
- **Cross-experiment near-synonyms.** PHYSLITE (ATLAS) ↔ NanoAOD (CMS) ↔ HiPT (LHCb-ish). Never use one without the experiment qualifier.
- **Concept/system name collisions.** "Trigger" is both a physics concept and a software system. "Run" is a framework, a data-taking period, and a verb. Always disambiguate.
- **Open-data vs internal-data leakage.** This is the worst failure mode for an assistant in this scope: an open-data skill confidently answering a question about an internal analysis (or vice versa) will produce wrong dataset names with high confidence. Every skill that touches data must state in its description whether it operates on **open data**, **collaboration-internal data**, or **both**, and refuse out-of-scope queries explicitly.
- **Parallel infrastructure verbs.** Rucio downloads, REANA fetches, DIRAC stages, EOS copies, CVMFS publishes. Always include the *infrastructure* in the trigger condition, not just the verb.
- **MC generator confusion.** Pythia, Herwig, MadGraph, Sherpa, PowhegBox, alpgen — all "generate events" but with different setup, tunes, and interpretation. Never write "use this for MC generation"; always specify the generator and the regime (LO, NLO, parton shower, matched, …).

---

## Principle 6: MCP tools follow the same rules

The MCP wrappers in your repo (`atlasopenmagic-mcp`, `cernopendata-mcp`, future Rucio/REANA wrappers) are routed by the same description-matching mechanism as skills. The router does not care whether a capability is implemented as a SKILL.md or an MCP tool. Therefore:

- MCP tool descriptions must follow the same writing rules as skill descriptions.
- Count MCP tools toward category density when deciding whether to nest.
- A category with 6 skills + 8 MCP tools is a 14-skill category for routing purposes.

---

## Principle 7: growth checklist (apply before merging any skill or MCP tool)

Whoever — human contributor or LLM — adds a skill must answer all of these:

1. Which **single** intent category does it belong to?
2. List the existing skills in that category and read their descriptions in full.
3. State the **unique trigger phrase** that distinguishes this skill from each neighbor. (Grep it across the library — it must appear nowhere else.)
4. State the **explicit scope boundary** disclaiming the closest neighbor.
5. If the category has a `ROUTER.md`, update it with a one-line summary of this skill.
6. Does this skill require permissions different from the agent that would call it? If yes, route through (or create) the appropriate sub-agent.
7. Add **3–5 prompts** to the eval harness that should select this skill, plus 2 prompts that should *not* select it.
8. Run the eval harness. If selection accuracy drops on **any pre-existing** skill, the new description overlaps too much — revise.

A skill that fails any of these checks does not get merged, regardless of how good its body is.

---

## Principle 8: eval harness — the only reliable cliff detector

The phase transition is sharp. Manual review will not catch it; you'll only notice when users report wrong answers. Build the regression suite from the start.

**Minimum viable harness:**

- 3–5 prompts per skill, written to be unambiguously about that skill
- A "should not match" set of 5–10 prompts that should pull no skill at all
- Run on every PR that adds, removes, or modifies a description (skill or MCP)
- Track top-1 selection accuracy over the full library

**Warning sign:** adding skill *N* in category X causes selection failures on a *different* pre-existing skill in category X. That is the confusability cliff arriving locally. The fix is description surgery, not adding more skills.

**Fancier-but-worth-it:** track per-skill selection precision and recall over time. A skill whose precision drops as the library grows is a description that has lost its uniqueness.

---

## What this guide does not solve

- **Multi-step workflows** ("find a dataset, stage it, run a fit, plot the result") still need either a planning agent or composite workflow skills that orchestrate atoms. The paper's findings are about single-step selection.
- **Cross-experiment unification** (running conceptually-equivalent ATLAS and CMS workflows). When this becomes real, add a `compare/` or `cross-experiment/` category — don't try to make individual skills experiment-agnostic.
- **Skill *content* quality.** A perfectly-described skill with a useless body still produces bad answers. This guide governs whether the *right* skill is invoked, not whether it does its job.
- **Tool authentication & secrets.** Permissions and credentials for Rucio, EOS, internal databases are out of scope here — handle them in agent definitions and MCP server configuration.

---

## References

- Li, X. (2026). *When Single-Agent with Skills Replace Multi-Agent Systems and When They Fail.* arXiv:2601.04748.
- Anthropic Engineering. *Equipping agents for the real world with agent skills.* (Oct 2025).
- Sweller, J. (1988). *Cognitive load during problem solving.* — for the cognitive-load framing the paper rests on.
- Miller, G. A. (1956). *The magical number seven, plus or minus two.* — for the bounded-capacity argument behind the "≤6 sub-agents" recommendation.

---

## Changelog

- *v0.1 — initial draft.* Scope: ATLAS Open Data → general CERN assistant. Eight intent categories, five-agent ceiling, eval-harness mandatory.
- *v0.1 — vendored into repo.* Copied verbatim from Obsidian vault on 2026-04-29 so the principles ship in git history alongside the skills they govern.
