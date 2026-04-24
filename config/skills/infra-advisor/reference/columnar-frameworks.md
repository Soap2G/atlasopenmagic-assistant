# Columnar analysis frameworks — picker

Short digest of the three columnar frameworks commonly used on CERN
infra, with the "when to pick" heuristic. All three can read ATLAS /
CMS Open Data via XRootD or HTTPS.

## Contents
- uproot + awkward (the Python substrate)
- coffea (analysis-oriented framework on top of uproot+awkward)
- ROOT RDataFrame (+ distributed RDataFrame)
- Scaling backends
- Picker

## uproot + awkward

Pure Python, reads ROOT files without a ROOT install. `awkward` gives
you jagged arrays (variable-length per-event structures).

- **Shape**: libraries, not a framework. You bring the control flow.
- **Pick when**: single-file or small-batch work, notebook
  exploration, teaching, or as the substrate for coffea.
- **Avoid when**: you want a framework to handle chunking, histogram
  bookkeeping, and scale-out for you.

```python
import uproot, awkward as ak
with uproot.open("root://eospublic.cern.ch//eos/opendata/atlas/...root") as f:
    t = f["physlite"]
    jet_pt = t["jet_pt"].array(library="ak")
```

## coffea

Analysis framework on top of uproot + awkward. Gives you a
`Processor` abstraction, bookkeeping for histograms, and pluggable
executors (local, futures, Dask, Parsl, Spark).

- **Shape**: framework. Write a processor class, hand it a fileset,
  pick an executor.
- **Pick when**: columnar analysis at scale, Open Data or Rucio-staged,
  and you want Dask scale-out on SWAN+HTCondor or coffea-casa.
- **Avoid when**: you're already deep in ROOT C++ and RDataFrame.

```python
from coffea import processor
from coffea.nanoevents import NanoAODSchema  # or PHYSLITESchema for ATLAS
# pick an executor: IterativeExecutor, FuturesExecutor, DaskExecutor
```

## ROOT RDataFrame

ROOT's high-level declarative analysis engine. C++ under the hood,
with Python bindings via PyROOT. JIT-compiles user lambdas.

- **Shape**: declarative graph (`Filter`, `Define`, `Histo1D`, ...).
- **Pick when**: user is already in the ROOT ecosystem, needs C++
  performance, or wants access to ROOT-only features (RooFit, TMVA,
  certain formats).
- **Avoid when**: user is Python-only with no ROOT stack, or the data
  lives in non-ROOT formats (parquet, HDF5).

```python
import ROOT
df = ROOT.RDataFrame("physlite",
                     "root://eospublic.cern.ch//eos/opendata/atlas/...root")
h  = df.Filter("jet_pt[0] > 30e3").Histo1D(("h","h",100,0,300e3), "jet_pt")
h.Draw()
```

### Distributed RDataFrame

Since ROOT 6.24 (stable by 6.30), RDataFrame has a **distributed**
mode that executes the same graph on Dask or Spark backends.

```python
import ROOT
RDF = ROOT.RDF.Experimental.Distributed.Dask

from dask.distributed import Client
client = Client(...)  # e.g. SwanHTCondorCluster + Client, see swan-htcondor.md

df = RDF.RDataFrame("physlite", files, daskclient=client)
h  = df.Filter("jet_pt[0] > 30e3").Histo1D(("h","h",100,0,300e3), "jet_pt")
h.Draw()   # materialises by running on the Dask workers
```

The **same script** runs locally (plain `ROOT.RDataFrame`) or
distributed (`RDF.Distributed.Dask.RDataFrame` with a Dask client).
This makes the SWAN+HTCondor ramp (see `swan-htcondor.md`) especially
clean for RDataFrame users.

## Scaling backends — matching frameworks to platforms

| Platform                        | uproot/awkward | coffea | RDataFrame (distributed) |
|---------------------------------|----------------|--------|--------------------------|
| Laptop / local                  | ✅             | ✅ (Iterative/Futures) | ✅ (single-node)  |
| SWAN interactive                | ✅             | ✅     | ✅                       |
| SWAN + HTCondor (Dask)          | with dask-awkward | ✅ (Dask exec) | ✅ (Dask backend) |
| coffea-casa (AF)                | ✅             | ✅ (native)     | possible but uncommon   |
| REANA serial step               | ✅             | ✅     | ✅                       |
| ml.cern.ch (for ML post-feature) | —             | —      | — (use after feature export) |

## Picker — one line each

- **Teaching / laptop / tutorial** → uproot + awkward.
- **Columnar scale-out in Python, CMS-style** → coffea + Dask.
- **ROOT shop, C++ performance, same code local-or-distributed** →
  RDataFrame (+ distributed RDataFrame for scale-out).
- **Decision rule**: match the user's existing ecosystem (Python vs
  ROOT) before optimising for speed. Porting across frameworks costs
  more than the scaling difference.
