# BrainAtlas — Agent Architecture Plan

Submission for Kaggle "AI Agents: Intensive Vibe Coding Capstone" (Agents for Good track).

## Problem & Vision

Interview coaching is expensive and inaccessible. BrainAtlas is a multi-agent system that conducts mock interviews, evaluates answers in real time, and produces a visual knowledge gap map — a living map of what the user still needs to learn, shrinking as they improve.

**Differentiator:** most submissions will be chatbots. BrainAtlas produces a Cytoscape.js knowledge graph that makes gaps visible and trackable across sessions.

---

## Competition Requirements

Must demonstrate at least 3 key concepts. Targeting:

1. **Multi-agent system (ADK / Antigravity)** — three sub-agents orchestrated by Antigravity
2. **MCP Server** — knowledge and persistence layer all agents call
3. **Deployability** — Cloud Run deployment, documented in README

Security features (prompt injection sanitization, RLS) noted in writeup as a bonus.

**Track:** Agents for Good (education / career advancement)

---

## Agent Architecture

Three sub-agents coordinated by the Antigravity orchestrator (ADK).

```
User (role + experience level)
        │
   Orchestrator (Antigravity / ADK)
   ┌────┴──────────────────────┐
   │                           │
Interviewer Agent        Evaluator Agent   ← runs after every answer, silently
   │                           │
   └──────────┬────────────────┘
              │
     Knowledge Mapper Agent   ← runs once at session end
              │
     Graph JSON + Study Plan
```

### Interviewer Agent

- Asks questions for the target role and domain
- Generates follow-up questions when Evaluator score falls below threshold
- Tools: `get_questions(role, domain, difficulty)`, `get_followup(answer, question, context)`

### Evaluator Agent

- Scores each answer against the rubric dimensions
- Checks which key concepts were mentioned, partially covered, or missed
- Missed key concepts become gap tags fed to the Knowledge Mapper
- Tools: `score_answer(question, answer, rubric, key_concepts)`, `extract_gaps(scores)`

### Knowledge Mapper Agent

- Aggregates all gap tags from the session
- Computes node size (severity × frequency) and edges (co-occurrence)
- Fetches study resources per gap tag
- Outputs graph JSON (for Cytoscape.js) + study plan markdown
- Tools: `build_gap_graph(gaps[])`, `get_resources(gap_tags[])`

### Orchestrator logic

- Deepens follow-up if Evaluator returns score < 5 on current question
- Moves to next question after follow-up or if score ≥ 5
- Triggers Knowledge Mapper after all questions are complete

---

## MCP Server Design

The MCP server is the knowledge and persistence layer. Agents call it; the frontend never touches it directly.

**Decisions:** See `DECISIONS.md` — D1 (storage: JSON + JSONL), D2 (FastMCP).

### File structure

```
mcp_server/
  server.py          # FastMCP app — 4 tool definitions
  db.py              # JSONL helpers: append_session(), read_sessions()
  test_mcp.py        # in-process smoke tests for all 4 tools
  requirements.txt
  data/
    questions.json   # question bank
    rubrics.json     # rubric definitions per question_type
    resources.json   # gap_tag → curated resource list
    sessions.jsonl   # runtime-created, append-only session log
```

### Tools

| Tool | Input | Output |
|---|---|---|
| `get_interview_questions` | role, domains[], difficulty, count | question list with key_concepts |
| `get_evaluation_rubric` | question_type | rubric object with dimensions + weights |
| `get_study_resources` | gap_tags[] | curated resource list per tag |
| `log_session_result` | session_id, role, scores, gaps[] | `{ok: true}` |

**Tool edge cases (prototype):**
- `get_interview_questions`: if fewer questions exist than `count`, returns all available — no error
- `get_evaluation_rubric`: unknown `question_type` returns empty rubric rather than erroring
- `get_study_resources`: unknown gap tags return empty list rather than erroring
- `log_session_result`: no deduplication — same session_id logged twice produces two records

`get_evaluation_rubric` returns both scoring dimensions AND the question's key concepts together, so the Evaluator has everything it needs in one call.

**Session log record shape:**
```json
{
  "session_id": "...",
  "role": "swe",
  "timestamp": "2026-06-30T10:00:00Z",
  "scores": { "q_001": 7, "q_002": 4 },
  "gaps": ["geospatial_indexing", "cap_theorem"]
}
```

### Resources (read-only)

- `questions://{role}/{domain}` — question bank
- `rubrics://{domain}` — scoring rubrics
- `resources://{topic}` — curated study materials

---

## Data Model

Production target (Supabase / Postgres). For prototype, these map 1:1 to JSON files — migration is a data load, not a redesign. See `DECISIONS.md` D1.

```
sessions
  id uuid PK
  user_id
  role
  experience_level
  status            -- in_progress | completed
  created_at
  completed_at

questions
  id uuid PK
  role
  domain            -- behavioral | system_design | product_sense | estimation
  difficulty        -- 1-5
  question_text
  rubric_id         -- FK to rubric type
  key_concepts      -- jsonb array: snake_case gap tags
  model_answer_summary
  common_mistakes   -- jsonb array

answers
  id uuid PK
  session_id        -- FK sessions
  question_id       -- FK questions
  answer_text
  score             -- 0-10
  gap_tags          -- text[]
  reasoning         -- evaluator explanation
  created_at

knowledge_gaps
  id uuid PK
  session_id
  user_id
  gap_tag
  severity          -- 1-3
  frequency         -- occurrences across sessions
  resolved          -- bool
  created_at

resources
  id uuid PK
  gap_tag
  title
  url
  type              -- article | video | book
  difficulty        -- 1-5
```

Graph nodes and edges are computed at query time from `knowledge_gaps`, not stored.

---

## Rubric Design

Rubrics are question-type specific, not generic. Each dimension has a weight; the weighted average produces the overall score.

### System Design

| Dimension | What it checks | Weight |
|---|---|---|
| requirements_clarification | Asked functional vs non-functional questions before designing? | 20% |
| scale_estimation | Estimated QPS, storage, bandwidth to size the system? | 15% |
| high_level_design | Architecture coherent — clear components and data flow? | 20% |
| data_model | Schema sound for the access patterns? | 15% |
| deep_dive_quality | Can go deep on one component when pushed? | 15% |
| trade_off_reasoning | Explained why this choice over alternatives? | 15% |

### Behavioral (STAR)

| Dimension | What it checks | Weight |
|---|---|---|
| situation_clarity | Context set concisely? | 15% |
| task_ownership | Their specific role clear? | 20% |
| action_specificity | What *they* did, not the team? | 30% |
| measurable_result | Quantified outcome? | 25% |
| relevance | Actually answered the question asked? | 10% |

### Product Sense

| Dimension | What it checks | Weight |
|---|---|---|
| user_identification | Right segment, clear empathy? | 20% |
| problem_framing | Framed before jumping to solutions? | 25% |
| prioritization_logic | Explained what to build and why? | 25% |
| trade_off_awareness | Acknowledged what they're not doing? | 15% |
| success_metrics | Can measure if it worked? | 15% |

### Estimation

| Dimension | What it checks | Weight |
|---|---|---|
| structured_approach | Top-down or bottom-up, not random? | 30% |
| assumptions_stated | Said assumptions out loud? | 25% |
| math_correctness | Arithmetic sound? | 20% |
| sanity_check | Gut-checked the final number? | 25% |

---

## Question Bank

**Decisions:** See `DECISIONS.md` — D3 (scope: SWE / system design only), D4 (gap tags from key_concepts), D5 (8 questions).

**For the hackathon:** hand-curated, system design only. Quality is controlled, gap tags are intentional, evaluation is defensible to judges.

**Future:** replace with an LLM pipeline that generates questions + key_concepts for any role/domain, validated by a second LLM pass. The data model supports this without changes.

### Question record structure

`key_concepts` are short snake_case strings that double directly as gap tags. The Evaluator matches the LLM's response against these — missed ones become gap tags fed to the Knowledge Mapper.

```json
{
  "id": "q_001",
  "role": "swe",
  "domain": "system_design",
  "difficulty": 4,
  "question_text": "Design a ride-sharing system like Uber.",
  "question_type": "system_design",
  "key_concepts": [
    "geospatial_indexing",
    "websocket_vs_polling",
    "eventual_consistency",
    "thundering_herd",
    "matching_service_isolation"
  ],
  "model_answer_summary": "Strong answers identify real-time location at scale as the core challenge, use a geo-index for O(1) nearby driver lookup, and articulate the consistency trade-off explicitly.",
  "common_mistakes": [
    "Naive SQL lat/lng query instead of a geo-index",
    "Polling every second without discussing WebSocket trade-offs",
    "Not addressing delayed location updates"
  ]
}
```

### 8 system design questions (prototype)

Each covers a distinct archetype so gap tags don't heavily overlap across questions:

| ID | Question | Core archetype |
|---|---|---|
| q_001 | Design a ride-sharing system (Uber) | Geospatial + real-time location |
| q_002 | Design a Twitter/X feed | Fan-out on write vs read, timeline |
| q_003 | Design a URL shortener | Hashing, redirect at scale |
| q_004 | Design a rate limiter | Token bucket / sliding window, distributed |
| q_005 | Design a notification system | Fan-out, push/pull, delivery guarantees |
| q_006 | Design a distributed cache (Redis-like) | Eviction, consistency, clustering |
| q_007 | Design a search autocomplete | Trie vs inverted index, prefix matching at scale |
| q_008 | Design a payment processing system | Idempotency, exactly-once, ledger integrity |

### Gap tag vocabulary (system design)

All tags below must have a corresponding entry in `resources.json` (2–3 resources each). 8 questions × ~4 tags each = ~30 unique tags, enough to produce a meaningful graph from one session.

```
geospatial_indexing, websocket_vs_polling, eventual_consistency,
thundering_herd, matching_service_isolation, fan_out_on_write,
fan_out_on_read, timeline_aggregation, hash_collision_handling,
redirect_at_scale, base62_encoding, token_bucket,
sliding_window_counter, distributed_rate_limiting, push_vs_pull_notifications,
delivery_guarantees, fan_out_scale, cache_eviction_policies,
cache_consistency, consistent_hashing, trie_vs_inverted_index,
prefix_matching, typeahead_ranking, idempotency_keys,
exactly_once_semantics, ledger_integrity, double_entry_bookkeeping,
cap_theorem, database_sharding, read_replicas
```

---

## Visualization (Cytoscape.js)

**Layout:** force-directed, target role as the center anchor.

**Visual encoding:**
- Node size → severity × frequency (bigger = worse gap)
- Node color → domain category (behavioral, system design, product sense, estimation)
- Node opacity → resolved vs unresolved (fades when marked studied)
- Edge weight → co-occurrence of two gap tags within the same session

**Interactions:**
- Click node → drawer opens with study resources for that gap
- Hover → tooltip shows which question exposed it
- "Mark as studied" → sets `resolved = true`, fades node
- Multi-session overlay → nodes shrink as gaps close (progress view)

---

## Security

| Area | Implementation |
|---|---|
| API keys | Server-side only, env vars, never in client bundle |
| Prompt injection | Sanitize user answer text before agent ingestion |
| Data isolation | Supabase RLS: users read/write only their own rows |
| Rate limiting | Max N sessions per user per day — middleware + Supabase policy |
| MCP server auth | Service token required, not exposed to frontend |
| PII / answers | Stored per session, not used for model training — noted in writeup |

---

## Tasks

### Task 1 — MCP Server + Question Bank

**Decisions:** See `DECISIONS.md` — D1, D2, D3, D4, D5.

- [ ] T1.1 Create `mcp_server/` directory and `requirements.txt` (`fastmcp`)
- [ ] T1.2 Write `data/questions.json` — 8 system design questions with full key_concepts
- [ ] T1.3 Write `data/rubrics.json` — system_design rubric (6 dimensions, weights sum to 100%)
- [ ] T1.4 Write `data/resources.json` — all ~30 gap tags, 2–3 resources each
- [ ] T1.5 Write `db.py` — `append_session()` and `read_sessions()` over `sessions.jsonl`
- [ ] T1.6 Write `server.py` — FastMCP app exposing all 4 tools
- [ ] T1.7 Write `test_mcp.py` — 5 assertions all passing (see below)

**Test assertions (`test_mcp.py`):**
1. `get_interview_questions` returns 8 questions, each with non-empty `key_concepts`
2. `get_evaluation_rubric("system_design")` returns 6 dimensions whose weights sum to 100%
3. `get_study_resources(["geospatial_indexing", "cap_theorem"])` returns 2 keys, each ≥1 resource
4. `log_session_result(...)` returns `{ok: true}` and appends to `sessions.jsonl`
5. `read_sessions()` returns the appended record

**Done when:** all 5 assertions pass and `fastmcp run server.py` starts without error.

---

### Task 2 — Evaluator Agent

- [ ] T2.1 Scaffold Evaluator agent with ADK
- [ ] T2.2 Implement `score_answer` — calls `get_evaluation_rubric` via MCP, scores per dimension
- [ ] T2.3 Implement `extract_gaps` — returns missed key_concepts as gap tags
- [ ] T2.4 Test in isolation: feed a known weak answer, assert expected gap tags are returned

**Done when:** Evaluator correctly identifies gaps from a scripted answer without the Interviewer running.

---

### Task 3 — Interviewer Agent

- [ ] T3.1 Scaffold Interviewer agent with ADK
- [ ] T3.2 Implement question selection — calls `get_interview_questions` via MCP
- [ ] T3.3 Wire Evaluator call after each answer — triggers silently, receives score + gaps
- [ ] T3.4 Implement follow-up logic — if score < 5, ask one follow-up before advancing
- [ ] T3.5 Test end-to-end: scripted 3-question session, verify follow-ups trigger correctly

**Done when:** a scripted session of 3 questions runs with correct follow-up behavior.

---

### Task 4 — Knowledge Mapper + Graph JSON

- [ ] T4.1 Scaffold Knowledge Mapper agent with ADK
- [ ] T4.2 Implement `build_gap_graph` — aggregates gaps, computes node size and edges
- [ ] T4.3 Implement `get_resources` — calls `get_study_resources` via MCP per gap tag
- [ ] T4.4 Output graph JSON in Cytoscape.js format + study plan markdown
- [ ] T4.5 Test: feed known gap list, assert graph JSON has correct nodes, edges, and sizes

**Done when:** graph JSON for a known gap list is valid Cytoscape.js input.

---

### Task 5 — Cytoscape.js Frontend

- [ ] T5.1 Add Cytoscape.js to Next.js app
- [ ] T5.2 Build graph page — renders nodes + edges from graph JSON
- [ ] T5.3 Implement click-to-drawer — opens study resources for clicked gap node
- [ ] T5.4 Implement hover tooltip — shows which question exposed the gap
- [ ] T5.5 Implement "Mark as studied" — fades node, updates resolved state

**Done when:** graph renders from a hardcoded JSON fixture and all interactions work.

---

### Task 6 — Orchestrator Wiring

- [ ] T6.1 Wire Orchestrator (Antigravity / ADK) to coordinate all three agents
- [ ] T6.2 Connect session start → Interviewer → Evaluator loop → Knowledge Mapper
- [ ] T6.3 Connect graph JSON output → frontend graph page
- [ ] T6.4 Run a full end-to-end session: real questions, real answers, real graph output

**Done when:** a complete session from question 1 to rendered gap graph works end-to-end.

---

### Task 7 — Deploy + Document

- [ ] T7.1 Containerize MCP server (`Dockerfile`)
- [ ] T7.2 Deploy to Cloud Run, verify tools are reachable
- [ ] T7.3 Deploy Next.js frontend to Vercel (or Cloud Run)
- [ ] T7.4 Write README — reproduction steps, architecture diagram, competition writeup

**Done when:** a judge can follow the README and run a session from scratch.

---

### Video Recording Checklist (Kaggle submission)

Record these moments as you build — a single edited video of 4–5 min is enough.

**Scene 1 — Antigravity vibe coding (~1 min)**
- [ ] Screen-record this chat: give Antigravity a task, show it writing code and running commands
- [ ] Show the diff/confirmation flow (Antigravity proposes → you approve)
- [ ] Show `agents-cli scaffold` or `agents-cli playground` being invoked from the chat
- *Covers: Antigravity, Agent Skills (Agents CLI)*

**Scene 2 — Multi-agent system running (~2 min)**
- [ ] Start the MCP server (`fastmcp run server.py`) — show it starting cleanly
- [ ] Run a scripted interview session via `agents-cli playground` or terminal
- [ ] Show the Evaluator scoring an answer silently and returning gap tags
- [ ] Show the Knowledge Mapper producing graph JSON
- *Covers: Multi-agent system (ADK), MCP Server*

**Scene 3 — Knowledge graph in the browser (~1 min)**
- [ ] Open the Cytoscape.js frontend, show the gap nodes rendered from the session
- [ ] Click a node — show the study resources drawer open
- [ ] Hit "Mark as studied" — show the node fade
- *Covers: end-to-end demo, differentiator vs plain chatbots*

**Scene 4 — Deployability (~30 sec)**
- [ ] Show `gcloud run deploy` output or the live Cloud Run URL responding
- [ ] Or show the Vercel deployment URL for the frontend
- *Covers: Deployability*

**Scene 5 — Security (optional, ~30 sec)**
- [ ] Show the `sanitize_input()` call in `server.py` in the editor
- [ ] Briefly mention API keys are server-side only (point to `.env` pattern in README)
- *Covers: Security features*

## Future Improvements

- **Real-time Map Updates:** Refactor `db.py` to support database `upserts` (updating existing session records instead of appending duplicates) so the Interviewer Agent can save its state after *every* answer. This will allow the frontend graph map to update in real-time while the user is actively answering questions, rather than waiting for the end-of-session reveal.
- **Custom Context API:** Add an API to allow users to upload arbitrary context (documents, notes) and tag them as personalized study resources.
- **Session Saving & Replay:** Allow users to save exceptionally good interview sessions as "model answer" resources to replay and learn from their own past successes.
- **Spaced Repetition & Memory Decay:** Implement a time-based decay function in the Knowledge Mapper so that older gaps increase in size over time if they aren't practiced, enforcing spaced repetition.
- **Multi-Tenant User Isolation:** Migrate from the local JSONL append-only log to a relational database (e.g., Postgres/Supabase) to store `user_id` on sessions and filter the graph output per-user.
- **Global Atlas View:** Add a dashboard mode to visualize the entire knowledge graph, complete with domain filtering (e.g., filter by engineering, general knowledge, etc.). This enables users to freely explore and strengthen their overall weak areas outside the context of a single assessment.
