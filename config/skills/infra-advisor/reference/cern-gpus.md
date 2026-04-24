# GPUs at CERN — infra digest

Distilled from the upstream overview. Read this when a user's goal
needs GPU access and you want to route them to the right service.

- Canonical source: https://clouddocs.web.cern.ch/gpu_overview.html
- Last refreshed against upstream: 2026-04-24

If the user asks a very specific GPU-driver / licensing / vGPU
question that isn't covered here, WebFetch the canonical source — this
digest intentionally keeps only the infra-level facts an advisor needs
to route a request.

## Services offering GPUs

| Service                 | Shape                              | Pick when…                                               |
|-------------------------|------------------------------------|-----------------------------------------------------------|
| **lxplus-gpu**          | SSH, shared, "limited isolation"   | Quick interactive debugging, `nvidia-smi` sanity check    |
| **HTCondor batch**      | Batch GPU jobs (Docker/Singularity)| Bursty training, many independent jobs, repeatable jobs   |
| **SWAN**                | Notebook, T4 GPUs                  | Interactive ML in Jupyter with CVMFS/EOS already mounted  |
| **ml.cern.ch (Kubeflow)** | Managed ML platform              | Training + serving, MLflow-style pipelines, long runs     |
| **GitLab CI/CD**        | GPU-enabled shared runners         | CI that trains/evaluates a model on every commit          |
| **OpenStack GPU flavors** | Dedicated VM, pass-through       | Custom stack or kernel, or you need a specific GPU model  |
| **Kubernetes / Magnum** | GPU-labeled cluster                | You're already on a managed k8s cluster                   |

**Default for analysis users**: start with **SWAN (T4)** or **ml.cern.ch**.
Escalate to HTCondor for batch; escalate to OpenStack only when the
platforms above don't fit.

## Quick access per service

### lxplus-gpu (interactive)
```bash
ssh -Y <username>@lxplus-gpu.cern.ch
nvidia-smi   # confirm the GPU is visible
```
Shared, no isolation. Don't pin long-running workloads here — use
batch or Kubeflow instead.

### HTCondor batch
Docs: https://batchdocs.web.cern.ch/gpu/index.html
Submit with a standard `condor_submit` file that requests GPUs. See
`examples.html` on the same site for templates.

### SWAN (T4 notebook)
1. Open https://swan.cern.ch
2. In the session form, pick **AlmaLinux9** as *Platform*.
3. Select a software stack that includes PyTorch / TensorFlow (the
   default stack tracks the latest).
4. Check the box exposing GPU resources.
5. On the notebook, `import torch; torch.cuda.is_available()` should
   return `True`.

### ml.cern.ch (Kubeflow)
Open https://ml.cern.ch, log in via CERN SSO, create a Notebook or
Pipeline with a GPU resource. Best for training → serving → pipeline
end-to-end.

### GitLab CI
Use the GPU-enabled shared runners — tag jobs accordingly. Docs:
https://gitlab.docs.cern.ch/docs/Build%20your%20application/CI-CD/Runners/k8s-gpu-runners/

### OpenStack flavors (exception path)

| Flavor         | GPU      | vCPU | RAM    | Disk   |
|----------------|----------|------|--------|--------|
| g2.5xlarge     | T4 ×1    | 28   | 168 GB | 160 GB |
| g3.xlarge      | V100S ×1 | 4    | 16 GB  | 64 GB  |
| g3.4xlarge     | V100S ×4 | 16   | 64 GB  | 128 GB |
| g4.p1.40g      | A100 ×1  | 16   | 120 GB | 600 GB |
| g4.p2.40g      | A100 ×2  | 32   | 240 GB | 1.2 TB |
| g4.p4.40g      | A100 ×4  | 64   | 480 GB | 2.4 TB |

Enable via a ServiceNow ticket to **GPU Platform Consultancy** with a
written use case. Default allocation is up to 4 months; longer leases
need justification. User installs drivers on the VM; monitoring is
the user's responsibility.

## Quota and scarcity — what to tell the user

- GPUs at CERN are **scarce and expensive**. Don't recommend an
  A100×4 VM for a toy job.
- Default grants are short (≤ 4 months) and require usage reports
  for renewal.
- Drivers update at most ~twice a year on shared services
  (lxplus-gpu, batch); pin any CUDA-dependent pipeline accordingly.

## Routing heuristic for the advisor

| User's goal                                           | First suggestion        |
|------------------------------------------------------|-------------------------|
| "Can I run this on a GPU real quick?"                | lxplus-gpu (SSH) + `nvidia-smi` |
| "Train a small/medium ML model in a notebook"         | SWAN (T4)              |
| "Train a model and serve an inference endpoint"       | ml.cern.ch (Kubeflow)  |
| "Run thousands of GPU jobs"                           | HTCondor batch GPUs    |
| "Evaluate a model on every PR"                        | GitLab CI GPU runners  |
| "I need an A100 for weeks with a custom CUDA stack"   | OpenStack g4.* flavor (ticket) |
