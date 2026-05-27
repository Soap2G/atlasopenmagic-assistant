---
name: htcondor
description: Use when the user wants to submit, monitor, inspect, or kill HTCondor batch jobs at CERN — `condor_submit` against a `.sub` file, `condor_q` for status, `condor_history` for finished jobs, `condor_rm` to kill, `condor_status` for pool health — plus the `htcondor` / `htcondor2` Python bindings. Covers `+JobFlavour` wall-time picks, multi-CPU / GPU requests, automatic Kerberos / AFS / EOS credential handling on lxplus / aiadm submit hosts. Detect availability via `command -v condor_submit`. Does NOT cover REANA workflow runs (use `reana` for status / logs, `reana-workflows` for authoring), CERN batch documentation lookup (use `cern-docs` with `source=batch`), proof that a finished job actually produced the expected outputs (use `verification-before-completion`), or multi-service infra recommendations (use `infra-advisor`). Disambiguator phrase: HTCondor lxbatch CLI & Python submission.
data_scope: both
experiment: all
---

# htcondor — CERN lxbatch submission & inspection

CERN's batch service is HTCondor. This skill covers operational use:
submitting jobs, checking status, retrieving logs, killing jobs, and the
Python bindings. For documentation queries about HTCondor at CERN, route
to `cern-docs` with `source=batch` instead.

Upstream documentation: https://batchdocs.web.cern.ch/

## When to load this skill

Load when the user wants to **act** on HTCondor at CERN:

- "Submit this job to lxbatch."
- "What's the status of my running condor jobs?"
- "Why is my job held?" / "Kill cluster 8901234."
- "Use the htcondor Python bindings to query my jobs."
- "Pick a JobFlavour for a 6-hour job."
- "Which schedd am I on?" / "My old cluster ID vanished after a schedd migration — find its history."

Do NOT load this skill for:

- **REANA workflows** — different engine (`reana` for lifecycle, `reana-workflows` for authoring).
- **Documentation lookup** — "what do the official CERN batch docs say about X" → `cern-docs` with `source=batch`.
- **Finished-job evidence** — "before I tell my supervisor my condor job is done, what should I check" → `verification-before-completion` (the meta-gate); this skill provides the *commands* it runs.
- **Multi-service stack recommendations** — "should I use HTCondor or REANA or SWAN for X" → `infra-advisor`.
- **SLURM at CERN** (Linux HPC) — different scheduler; not yet covered by lumi. Route to `cern-docs` for now.

## Environment detection

Check before generating commands:

```bash
command -v condor_submit       # → /usr/bin/condor_submit on lxplus / lxbatch submit hosts
klist                          # confirm a valid Kerberos ticket; if missing, run `kinit`
python -c "import htcondor2"   # confirm the Python bindings are available (HTCondor ≥ 24.12 at CERN)
```

If `condor_submit` is missing, the user is not on a submit host — redirect them to lxplus.cern.ch or aiadm, do NOT try to shell out to a non-existent command.

## Submit-file basics

A minimal CERN-flavoured `.sub` file:

```
executable            = hello_world.sh
arguments             = $(ClusterId) $(ProcId)
output                = output/hello.$(ClusterId).$(ProcId).out
error                 = error/hello.$(ClusterId).$(ProcId).err
log                   = log/hello.$(ClusterId).log
+JobFlavour           = "longlunch"
queue
```

Quirks that bite:

- HTCondor will **not** create `output/`, `error/`, `log/` for you. Create them before submit, or use `initialdir`.
- The `+JobFlavour` value must be **double-quoted** in the submit file.
- The `executable` script must be executable (`chmod +x`).
- Multi-job: replace `queue` with `queue N` and use `$(ProcId)` to distinguish.

## JobFlavour wall-time picks

CERN-specific shorthand. Set with `+JobFlavour = "<name>"`. Maximum wall-time:

| Flavour | Max wall-time |
|---|---|
| `espresso` | 20 minutes (default if unspecified) |
| `microcentury` | 1 hour |
| `longlunch` | 2 hours |
| `workday` | 8 hours |
| `tomorrow` | 1 day |
| `testmatch` | 3 days |
| `nextweek` | 1 week |

Alternative — set the wall-time directly: `+MaxRuntime = <seconds>`. Jobs that exceed the limit are terminated; partial stdout/stderr is **not** copied back.

Source: https://batchdocs.web.cern.ch/local/submit.html#job-flavours

## Resource requests

Default slot: 1 CPU, 3 GB memory, 20 GB disk.

To request more CPUs:

```
RequestCpus = 4   # → 4 CPUs, 12 GB memory, 80 GB disk (system scales at 3 GB/core)
```

Memory is a **soft** limit — jobs are killed under memory pressure on the node. If you need more memory, request more cores (don't request 8 GB on a 1-CPU slot).

Multicore jobs of **4+ cores** are scheduled faster than 2–3-core jobs (the system needs to defragment slots; smaller multicore requests fall through the cracks).

GPUs: see https://batchdocs.web.cern.ch/gpu/ for the `request_gpus` directive and current quota.

## Authentication, AFS, and EOS

The submit machines (lxplus, aiadm, …) **automatically** call `batch_krb5_credential` on submit, which manages:

- Kerberos tickets (renewed for the job).
- AFS tokens (via `aklog`).
- EOS FUSE authentication (via `eosfusebind`).

The user just needs a valid Kerberos ticket on the submit host (`kinit` if `klist` is empty). No `use_x509userproxy` boilerplate is needed for AFS/EOS access — it's automatic at CERN.

For jobs that need a Grid x509 proxy (rare at lxbatch — usually for Rucio / WLCG storage), add `use_x509userproxy = true` and ensure `voms-proxy-init` was run.

Source: https://batchdocs.web.cern.ch/concepts/kerberos.html

## Core CLI commands

Every command supports `-help`. Use `-json` (or `-af`) for parseable output suitable for the model to read.

| Command | Purpose | LLM-friendly form |
|---|---|---|
| `condor_submit hello.sub` | Submit a job (or job cluster). Prints the ClusterId. | `condor_submit hello.sub -terse` |
| `condor_q` | List your queued / running jobs. | `condor_q -json` or `condor_q -af ClusterId ProcId JobStatus QDate` |
| `condor_q -hold` | Show held jobs and their hold reason. | `condor_q -hold -af ClusterId ProcId HoldReason` |
| `condor_q <ClusterId>` | Status of a specific cluster. | `condor_q <ClusterId> -json` |
| `condor_history` | List your finished / completed jobs (recent history). | `condor_history -json -limit 50` |
| `condor_history <ClusterId>` | Final state + ExitCode for a specific cluster. | `condor_history <ClusterId> -af ExitCode ExitBySignal CompletionDate` |
| `condor_rm <ClusterId>` | Remove (kill) a job or cluster. | — |
| `condor_rm <user>` | Remove ALL your jobs. Use carefully. | — |
| `condor_wait <log_file> <ClusterId>` | Block until the cluster completes. | — |
| `condor_status` | Pool health (machines, slots, load). | `condor_status -json` |

`JobStatus` integer values (referenced in `-json` and `-af` output):
1 = Idle, 2 = Running, 3 = Removed, 4 = Completed, 5 = Held, 6 = Transferring Output, 7 = Suspended.

## Python bindings (htcondor / htcondor2)

CERN runs HTCondor ≥ 24.12 — both APIs are available. **Prefer `htcondor2`** for new code (forward-compatible).

```python
import htcondor2 as htcondor
import classad2 as classad

# Submit a job
sub = htcondor.Submit({
    "executable": "/path/to/script.sh",
    "arguments": "$(ClusterId) $(ProcId)",
    "output": "output/job.$(ClusterId).$(ProcId).out",
    "error":  "error/job.$(ClusterId).$(ProcId).err",
    "log":    "log/job.$(ClusterId).log",
    "+JobFlavour": '"longlunch"',     # note: value is a quoted string
    "request_cpus": "1",
    "MY.SendCredential": "True",      # v2 takes strings; v1 took booleans
})

schedd = htcondor.Schedd()
result = schedd.submit(sub)
cluster_id = result.cluster()
print(f"submitted cluster {cluster_id}")

# Query my jobs
for job in schedd.query(
    constraint='Owner == "myuser"',
    projection=["ClusterId", "ProcId", "JobStatus", "Cmd"],
):
    status = htcondor.JobStatus(job.get("JobStatus")).name
    print(f'{job["ClusterId"]}.{job["ProcId"]} {status} {job.get("Cmd")}')
```

Token bootstrap (only needed once per session if the submit host hasn't done it automatically):

```python
credd = htcondor.Credd()
credd.add_user_cred(htcondor.CredTypes.Kerberos, None)
```

Source: https://batchdocs.web.cern.ch/local/pythonapi.html

## Service limits

- **No limit** on submission rate per user.
- **10,000 simultaneously running jobs** per user (scheduler cap).
- Held jobs are **auto-removed after 24 hours**.
- A job that is **restarted 10 times** is auto-removed.

Source: https://batchdocs.web.cern.ch/concepts/service-limits.html

## Schedd context (which scheduler am I using?)

CERN's HTCondor pool has multiple schedds. For most users the submit
host (lxplus, aiadm) picks one automatically and you do not have to
think about it. Three situations make it matter: a migration moves
your old ClusterIds to another schedd, a large workload exceeds the
default schedd's capacity, or you want to control your default
explicitly.

| Question | Command / action |
|---|---|
| Which schedd is my current job on? | `condor_q -af ClusterId GlobalJobId` — the prefix of `GlobalJobId` is the schedd hostname. |
| Which schedds are reachable right now? | `condor_status -schedd` — lists schedds with queue depth and load. |
| My old ClusterId disappeared after a migration | `condor_history -name <old-schedd-host> <ClusterId>` — finished jobs may still be queryable there. See https://batchdocs.web.cern.ch/troubleshooting/scheddmigration.html. |
| I need to submit >>10 k jobs in one campaign | Switch to a Spool schedd (`-spool` flag) or an EosSubmit schedd. See https://batchdocs.web.cern.ch/local/spool.html and https://batchdocs.web.cern.ch/local/eossubmit.html. |
| I want to control which schedd I submit to | Use the `myschedd` tool to manage your default assignment. See https://batchdocs.web.cern.ch/local/myschedd.html. |

For configuration / management depth beyond this table — what
`myschedd` flags do, the full migration recovery procedure, EosSubmit
quirks — fall through to the `cerndocs` MCP (`source=batch`); the
chain pattern is described below.

## Common pitfalls

The CERN docs list these as the recurring causes of grief — apply them as preflight checks before launching big campaigns:

1. **Test on a small N before submitting many.** One job that fails for a trivial reason × 10,000 = wasted slots and your fairshare priority drops.
2. **Do not use `getenv = True`.** Inherits your interactive shell environment into the job; non-reproducible, breaks when the submit host's env shifts.
3. **Be careful with input/output data paths.** `transfer_input_files` for small inputs; for large I/O use AFS/EOS paths directly; don't write to your home AFS volume from inside a job (size/quota grief).
4. **Don't spawn more threads/processes than `RequestCpus`.** HTCondor enforces the cpu count; over-threading slows everyone down and may get the job held.
5. **Don't stress external services.** Jobs hammering EOS, CVMFS, or AFS in a tight loop will degrade those services for everyone. Cache or pre-stage inputs.

Source: https://batchdocs.web.cern.ch/troubleshooting/pitfalls.html

## Recipes

### Submit a job and wait for it

```bash
mkdir -p output error log
condor_submit hello.sub        # -> CLUSTER_ID
condor_wait log/hello.$(grep ClusterId log/*.log | awk '{print $NF}').log
condor_history <CLUSTER_ID> -af ExitCode ExitBySignal CompletionDate
```

### "What's my state right now?"

```bash
condor_q -af:h ClusterId ProcId JobStatus RemoteHost JobStartDate
condor_q -hold -af:h ClusterId ProcId HoldReason
```

### Inspect a specific finished cluster

```bash
condor_history <ClusterId> -json | jq '.[] | {ClusterId, ProcId, ExitCode, ExitBySignal, CompletionDate, HoldReason}'
```

### Kill a misbehaving cluster

```bash
condor_rm <ClusterId>
# Verify:
condor_q <ClusterId>     # should now show JobStatus 3 (Removed) or be gone
```

### After a finished job — proof of completion

Hand off to `verification-before-completion`. The evidence checklist for an HTCondor job:
- `condor_history <ClusterId> -af ExitCode` shows `0`.
- Output ROOT / text files exist with non-zero size.
- Cutflow row counts match expectations (if applicable).

`condor_q` reporting "Completed" alone is not proof — read the exit code.

## Drilling deeper into the docs (composition with `cern-docs`)

This skill carries the **common-case** knowledge inline: the four CLI
verbs, the JobFlavour table, service limits, the Kerberos automation,
the Python-bindings pattern, the most common pitfalls and the schedd
context. That is roughly 80 % of what users actually ask.

For the other 20 % — canonical detail beyond what is here, newer or
edge-case pages such as ATLAS-CAF tier-0 specifics, the full DAGMan
tutorial, GPU quota tables, or any page that has changed since this
skill was last reviewed — **call the `cerndocs` MCP directly from this
skill's recipe flow**:

```text
cerndocs_search_docs(source="batch", query="<topic>", limit=20)
# pick the top hit URL
cerndocs_fetch_doc(url="<that URL>", mode="markdown")     # if the source is Class A
# (batch is Class B → snippets-only; raise the limit and read from search hits)
```

The `htcondor` skill and the `cern-docs` skill are designed to
**compose**: `htcondor` for the *act* (submit / inspect / kill /
schedd-management commands), `cerndocs` MCP for the *canonical word*
when the act requires a detail this skill does not carry. Routing-time
NOT-covered redirects keep the router from picking the wrong skill on
ambiguous prompts; at execution time, any loaded recipe is free to call
`cerndocs_search_docs` to ground its answer.

When you do drill into the docs, cite the public
`https://batchdocs.web.cern.ch/...` URL in the user reply — never the
MCP-internal source ID.

## Output rules — what makes it into the user reply

- Cite **command names** (`condor_submit`, `condor_q -json`, `condor_history -af`). The user can re-run them.
- Cite **batchdocs.web.cern.ch URLs** when pointing at the canonical reference, NOT `cern-docs` internal source IDs.
- Quote actual command output when the user runs commands; never invent ExitCode / status / HoldReason values.

## Recovery behaviour

If a command fails (Kerberos missing, schedd unreachable, permission denied):

1. Run `klist` — if no ticket, `kinit` and retry.
2. Check schedd reachability: `condor_status -schedd | grep <hostname>`.
3. For "permission denied" on EOS/AFS: verify `eosfusebind` / `aklog` ran (they should automatically on submit hosts).
4. Surface the **actual error** to the user, not a paraphrase. Per critical rule 6.
