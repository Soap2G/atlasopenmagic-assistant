---
name: verification-before-completion
description: Use BEFORE claiming any long-running CERN compute step finished — REANA workflow runs, HTCondor / lxbatch jobs, xrdcp / rucio download transfers, uproot iterate loops over many files, distributed Dask reductions, multi-stage REANA pipelines, ROOT macros that produce output files. Block the "done" claim until concrete evidence is shown: `reana-client status` output, condor `JobStatus`, exit code, output file size from `ls -la` / `xrdfs stat`, cutflow row counts, fit convergence. The body of the skill, vendored from obra/superpowers, gives the gate function and worked dialogues. Disambiguator phrase: completion-evidence gate.
data_scope: both
---

## CERN verifiable plan format

When planning a multi-step analysis or workflow, emit a verifiable plan
**before** executing. Each step names a concrete check that proves it
succeeded. Example shape:

```
1. Submit REANA workflow          → verify: reana-client status shows "finished"
2. Download output ROOT file      → verify: ls -lh shows non-zero size, xrdfs stat matches
3. Run uproot loop over output    → verify: cutflow table row counts match expected N_events
4. Produce normalised histogram   → verify: integral matches cross_section × lumi within 1%
```

Concrete checks for CERN workloads:

| Step type | Concrete check |
|---|---|
| REANA workflow | `reana-client status` → `finished`; step logs show exit 0 |
| HTCondor / lxbatch job | `condor_q` or `bjobs` exit; output file present with non-zero size |
| `xrdcp` / Rucio download | `ls -lh` / `xrdfs stat` size matches source; optional checksum |
| `uproot` iterate loop | Cutflow row counts printed per file; no silent exception swallowing |
| Fit / pyhf | Convergence status (`minuit.valid`); NLL value printed |

"Should work" and "looks correct" are not concrete checks.
