---
name: verification-before-completion
description: Use BEFORE claiming any long-running CERN compute step finished — REANA workflow runs, HTCondor / lxbatch jobs, xrdcp / rucio download transfers, uproot iterate loops over many files, distributed Dask reductions, multi-stage REANA pipelines, ROOT macros that produce output files. Block the "done" claim until concrete evidence is shown: `reana-client status` output, condor `JobStatus`, exit code, output file size from `ls -la` / `xrdfs stat`, cutflow row counts, fit convergence. The body of the skill, vendored from obra/superpowers, gives the gate function and worked dialogues. Disambiguator phrase: completion-evidence gate.
data_scope: both
---
