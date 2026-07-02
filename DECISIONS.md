# BrainAtlas — Architecture Decisions

Decisions made for speed-to-demo. Each entry documents what was chosen, what was deferred, and what to revisit for production.

---

## Task 1: MCP Server + Question Bank

### D1 — Storage backend: JSON files + JSONL session log

**Chosen:** Static JSON files for questions, rubrics, and study resources. A JSONL file (newline-delimited JSON) for session logs — one record appended per completed session.

**Why for demo:** Zero infra. Judges can `git clone && pip install && python server.py` with no accounts, no env vars for storage, no schema migrations. JSONL is persistent on disk — survives process restarts, which is what the multi-session graph view needs.

**Tradeoffs accepted:**
- No concurrent write safety on the JSONL log — two simultaneous sessions writing could interleave bytes. Acceptable for a single-user demo.
- No SQL queries over the question bank — Python dicts + list comprehension is fast enough at 8–30 questions.
- Session log grows unboundedly — fine for demo, would need rotation or DB in production.

**What to swap in for production:** Supabase (Postgres) with RLS. The data model in `plan.md` maps 1:1 to the JSON schema here — migration is a data load, not a redesign.

---

### D2 — MCP framework: FastMCP

**Chosen:** `fastmcp` Python library.

**Why for demo:** Decorator-based tool registration (`@mcp.tool()`) is ~5 lines per tool vs ~20 with the raw `mcp` SDK. Supports in-process call mode — tools can be tested as plain async functions without spinning up a transport layer.

**Tradeoffs accepted:**
- Not the official Anthropic MCP SDK — FastMCP is community-maintained.
- If FastMCP falls behind the MCP spec, tool definitions may need rewriting.

**What to swap in for production:** Evaluate official `mcp` SDK once it stabilizes, or keep FastMCP if it stays current.

---

### D3 — Scope: SWE / System Design only (prototype)

**Chosen:** One role (Software Engineer), one domain (System Design), 8 questions.

**Why for demo:** Focused story, judges understand the domain, 8 well-curated questions with rich key_concepts produce a more compelling graph than 30 thin ones. Rubric is already fully defined.

**Tradeoffs accepted:**
- Demo only shows system design gaps — behavioral, product sense, estimation excluded from the graph.
- Less impressive breadth on paper, but the depth of evaluation is higher.

**What to add for production:** Behavioral (STAR rubric already in plan.md), Product Sense, Estimation. The data model and MCP tools are domain-agnostic — adding a domain is: write questions → add gap tags → add resources.

---

### D4 — Gap tags: derived from key_concepts, not LLM-inferred

**Chosen:** Each question stores `key_concepts` as a list of tagged strings. Gap tags are set to the missed `key_concepts` directly — no LLM inference step.

**Why for demo:** Deterministic, auditable, no hallucination risk in the evaluation layer. Judges can inspect exactly why a gap tag appeared.

**Tradeoffs accepted:**
- Tag vocabulary is fixed at question-authoring time — LLM answers can't surface gaps the author didn't anticipate.
- Requires more upfront work in question curation (key_concepts must be specific and tag-friendly).

**What to add for production:** A second LLM pass that normalizes free-form Evaluator output against the canonical tag list, with a fallback to create new tags (human-reviewed before publishing).

---

### D5 — Question count: 8 system design questions for prototype

**Chosen:** 8 questions covering distinct system archetypes (location-based, feed, URL shortener, rate limiter, notification, cache, search, payments).

**Why for demo:** 8 questions × 5–8 key_concepts each = 40–64 potential gap nodes in the graph. Enough to show a meaningful, non-trivial knowledge map from a single session.

**Tradeoffs accepted:**
- A user who has studied extensively will have a sparse graph after one session (looks underwhelming).
- No difficulty progression in v1 — all questions are difficulty 4.

**What to add for production:** ~30 questions per domain, difficulty 2–5, with adaptive selection based on session history.

---

## File Structure

```
mcp_server/
  server.py            # FastMCP app — all 4 tool definitions
  data/
    questions.json     # question bank (system design, 8 questions)
    rubrics.json       # system_design rubric (dimensions + weights)
    resources.json     # gap_tag → curated resource list
    sessions.jsonl     # append-only session log (created at runtime)
  db.py                # JSONL read/write helpers
  test_mcp.py          # in-process smoke tests for all 4 tools
```

---

### D6 — Graph Visualization: Global Atlas View

**Chosen:** The `/api/graph/{session_id}` endpoint computes the graph by iterating over *all* historical gaps from *all* sessions stored in `sessions.jsonl`. Node sizes scale dynamically based on the total historical frequency of the gap across the entire user's history.

**Why for demo:** Provides a visually stunning and massively interconnected "Global Atlas" that proves the system's ability to persistently track knowledge gaps over time. Showing just the most recent session's gaps often resulted in sparse, underwhelming graphs (e.g. 1-2 nodes) if the user performed well on a specific topic.

**Tradeoffs accepted:**
- Can become visually cluttered (a "hairball") for power users with extensive history, as there is currently no filtering by domain or time period in the UI.

**What to swap in for production:** Introduce UI toggles to switch between "Recent Session View" and "Global Atlas View", and add filters to isolate specific domains (e.g., engineering vs medical).
