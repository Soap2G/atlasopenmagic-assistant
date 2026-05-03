---
name: cern-docs
description: Use when the user asks how a CERN service or ATLAS framework operates and the answer should come from canonical operator documentation — HTCondor / lxbatch submission, SWAN session settings and HTCondor pool, CERN Cloud (OpenStack) flavors and quotas, ML@CERN training and serving, ATLAS Athena / ASG / Tier-0 / databases, ATLAS computing and grid production. Backed by the `cerndocs` MCP (`search_docs` for BM25 search, `fetch_doc` for one page) over 7 indexed sources: atlas-sft, atlas-computing, atlas-databases, batch, cloud, ml, swan. Does NOT cover Open Data dataset / recid / DOI lookup (use `cern-opendata` or `atlas-opendata`), live job-state inspection (use `reana` or shell tools), or multi-service infra recommendations (use `infra-advisor`). Disambiguator phrase: CERN MkDocs full-text search.
data_scope: both
---

# cern-docs — canonical CERN service & ATLAS-software documentation lookup

Upstream MCP: https://cern-mkdocs-mcp.app.cern.ch/mcp

This skill is a thin wrapper around the `cerndocs` MCP server. The
server indexes the search payloads of seven MkDocs-based CERN sites
(BM25 cached for 24 h) and pulls page bodies live from the upstream
git repos on demand.

## When to load this skill

The user wants to know how a CERN service or ATLAS framework operates
**as documented**. Examples:

- "How do I submit an HTCondor job from lxplus?"
- "What does the SWAN session timeout default to?"
- "Where are the GPU flavors documented in CERN Cloud?"
- "How does ATLAS Athena versioning work?"
- "What endpoints does ml.cern.ch's serving expose?"

Do NOT load this skill for:

- **Open Data dataset / recid lookup** → use `cern-opendata`
  (portal records) or `atlas-opendata` (DSIDs, MC metadata).
- **Live job-state inspection** (a *running* REANA workflow, a
  *current* condor job's status) → use `reana` or the shell tools.
- **Composite multi-service infra recommendations** ("what stack
  should I use to do X end-to-end") → use `infra-advisor`.

## Source IDs

The MCP exposes one `source` parameter to route queries to one of
seven indexed sites. Pick the source that matches the user's domain;
when ambiguous, search more than one — each source is its own BM25
index and a wrong-source query can miss a hit silently.

| `source` | Site | Topic | `fetch_doc`? |
|---|---|---|---|
| `atlas-sft` | atlas-software.docs.cern.ch | Athena, ASG, ATLAS software | ✅ |
| `atlas-computing` | atlas-computing.docs.cern.ch | Tier-0, grid, MC production | ✅ |
| `atlas-databases` | atlas-databases.docs.cern.ch | COOL, AMI, conditions DBs | ✅ |
| `batch` | batchdocs.web.cern.ch | HTCondor / lxbatch | ❌ snippets only |
| `cloud` | clouddocs.web.cern.ch | OpenStack, CERN Cloud, GPUs | ❌ snippets only |
| `ml` | ml.docs.cern.ch | ML@CERN, Kubeflow, serving | ❌ snippets only |
| `swan` | swan.docs.cern.ch | SWAN Jupyter sessions | ❌ snippets only |

The MCP also exposes a `docs://sources` resource that lists the
registered sources at request time — call it if you suspect the source
list has grown beyond the seven above.

## Tool usage

### Step 1 — always: `search_docs`

`search_docs(query, source, limit=10)` — BM25 search. Returns title + URL +
200-char snippet only. **Token-cheap.** Always start here regardless of source.

### Step 2 — source-class dependent

The seven sources split into two classes based on how their content is hosted:

**Class A — Markdown-backed (`atlas-sft`, `atlas-computing`, `atlas-databases`)**
These are MkDocs sites with a `docs/` directory accessible via the GitLab Files
API. `fetch_doc` can retrieve full page bodies:

- `fetch_doc(url, mode="outline")` — headings only. Confirm the right page first.
- `fetch_doc(url, mode="sections:<heading>")` — one section; use when the
  question is scoped to a known heading.
- `fetch_doc(url, mode="markdown")` — full page body. Most expensive; use only
  when the question genuinely needs the whole page.

**Class B — search-only (`batch`, `cloud`, `ml`, `swan`)**
These sources are hosted outside the MkDocs GitLab path resolver. `fetch_doc`
returns "No matching source file" for all URLs from these sources.

- Use `search_docs` with a higher limit (`limit=20`) to cast a wider net.
- The 200-char snippet per result is the only retrieval mechanism available.
- When the question is narrow (e.g. a specific config option), rephrase and
  re-run rather than increasing the limit further.
- Cite the public URL from the search hit even when you can't fetch the body.

## Output rules — what makes it into the user reply

- Cite the **public docs URL** that the search hit returned (e.g.
  `https://swan.docs.cern.ch/sessions/`). The user can open it.
- Quote the relevant prose from the fetched body inline; do not link
  the user to the MCP URL or to any internal page identifier.
- If the MCP returns a Recovery Guide (auth-gated source with no
  token, unknown source ID), surface the recovery instructions to
  the user verbatim — they are operator-grade help text.

## Example flows

**"How does Athena versioning work?"** (atlas-sft — Class A)
1. `search_docs(query="Athena release versioning", source="atlas-sft")`
2. Pick the top hit, `fetch_doc(url=<hit URL>, mode="outline")` to confirm.
3. `fetch_doc(url=<hit URL>, mode="markdown")` for the full body.
4. Quote the relevant section, cite the URL.

**"How do I submit a condor job from lxplus?"** (batch — Class B, search-only)
1. `search_docs(query="submit job from lxplus", source="batch", limit=20)`
2. Extract the answer from snippets; cite the returned URL.
3. If snippets are thin, re-query with a tighter phrase:
   `search_docs(query="condor_submit .sub file lxplus", source="batch", limit=20)`.

**"What's the default SWAN session timeout?"** (swan — Class B, search-only)
1. `search_docs(query="session timeout default", source="swan", limit=20)`
2. Extract from snippets; cite the returned URL.
3. *(fetch_doc is not available for swan — snippets are the ceiling.)*

**Cross-source question** ("compare HTCondor on batch vs SWAN's HTCondor pool"):
run `search_docs` separately against `batch` and `swan`, present both.
Don't let the BM25 ranker silently hide one source.
