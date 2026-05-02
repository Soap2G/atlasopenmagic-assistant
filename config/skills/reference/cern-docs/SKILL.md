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

| `source` | Site | Topic |
|---|---|---|
| `atlas-sft` | atlas-software.docs.cern.ch | Athena, ASG, ATLAS software |
| `atlas-computing` | atlas-computing.docs.cern.ch | Tier-0, grid, MC production |
| `atlas-databases` | atlas-databases.docs.cern.ch | COOL, AMI, conditions DBs |
| `batch` | batchdocs.web.cern.ch | HTCondor / lxbatch |
| `cloud` | clouddocs.web.cern.ch | OpenStack, CERN Cloud, GPUs |
| `ml` | ml.docs.cern.ch | ML@CERN, Kubeflow, serving |
| `swan` | swan.docs.cern.ch | SWAN Jupyter sessions |

The MCP also exposes a `docs://sources` resource that lists the
registered sources at request time — call it if you suspect the source
list has grown beyond the seven above.

## Tool usage — progressively more expensive

1. `search_docs(query, source, limit=10)` — BM25 search. Returns
   title + URL + 200-char snippet only. **Token-cheap.** Always start
   here unless the user already gave you a URL.
2. `fetch_doc(url, mode="outline")` — headings only. Use to confirm
   the right page before paying for the full body.
3. `fetch_doc(url, mode="sections:<heading>")` — one section. Use
   when the question is scoped to a known sub-heading.
4. `fetch_doc(url, mode="markdown")` — full body. Most expensive;
   reach for it only when the question genuinely needs the page.

## Output rules — what makes it into the user reply

- Cite the **public docs URL** that the search hit returned (e.g.
  `https://swan.docs.cern.ch/sessions/`). The user can open it.
- Quote the relevant prose from the fetched body inline; do not link
  the user to the MCP URL or to any internal page identifier.
- If the MCP returns a Recovery Guide (auth-gated source with no
  token, unknown source ID), surface the recovery instructions to
  the user verbatim — they are operator-grade help text.

## Example flows

**"How do I submit a condor job from lxplus?"**
1. `search_docs(query="submit job from lxplus", source="batch")`
2. Pick the top hit, `fetch_doc(url=<top hit URL>, mode="markdown")`.
3. Quote the submission snippet, cite the URL.

**"What's the default SWAN timeout?"**
1. `search_docs(query="session timeout", source="swan", limit=5)`
2. `fetch_doc(url=<top hit URL>, mode="sections:Session timeout")` —
   if the heading exists in the outline.
3. Otherwise `mode="markdown"`. Cite the URL.

**Cross-source question** ("compare HTCondor on batch vs SWAN's
HTCondor pool"): run `search_docs` separately against `batch` and
`swan`, present both. Don't let the BM25 ranker hide one source.
