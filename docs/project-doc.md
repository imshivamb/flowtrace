# FlowTrace — Multi‑Agent Workflow & Observability (LangGraph)‑Agent Workflow & Observability (LangGraph)

**Execution mode:** Balanced V1 (15–18 days). Focus: production‑grade traceability, fallbacks, exact‑match cache, simple router, polished demo.

---

## 1) One‑Pager (Founder/Engineering Voice)

**Problem** — AI agent workflows are opaque. Teams can’t see *why* a run took a path, *where* it failed, or *how much* it cost. Debugging takes hours; costs drift.

**Audience** — AI startups, LLM platform teams, founding engineers who need reliability + visibility.

**Promise** — Build, run, and debug multi‑step agent workflows with live traces, per‑step cost/latency/tokens, retries, and provider fallbacks. Repeat inputs hit cache.

**Non‑Goals (V1)** — No marketplace/billing/roles. No semantic KB builder. No heavy A/B UI.

**Definition of Done** — Create/edit workflow → run → watch live SSE trace → open any step to see inputs/outputs/tokens/cost/latency → retries/fallbacks visible → summary totals correct → repeated run shows cache hit.

---

## 2) Feature Spec — Balanced V1 (Must‑Haves Only)

1. **Workflow Builder (React Flow)** — Node palette: `llm`, `tool`, `router`. Connect edges; basic node config panel; JSON persists.
2. **Executor (LangGraph)** — Topological order; sequential by default; safe parallel within level (opt‑in). Backoff retries for transient errors.
3. **Traceability** — Emit `llm.request/response`, `tool.request/response`, `log`, `retry`, `cache.hit` with timestamps. Persist all.
4. **Live Streaming (SSE)** — Per‑run event stream renders timeline in UI.
5. **Cost/Usage Accounting** — Pricing map per model. Tokens, latency, cost at step + rolled up to run.
6. **Fallbacks** — OpenAI → Anthropic on eligible failures/timeouts. Logged in trace.
7. **Exact‑Match Cache** — Key = (provider, model, system, prompt, inputs). Hit short‑circuits step and logs `cache.hit`.
8. **Router Node** — Simple boolean/branch rule (`when:` expression) to gate edges. Minimal but demonstrable.
9. **Guardrails** — Limits on nodes/run, tokens/run, run duration; error surfaces clearly.

---

## 3) Workflow JSON Spec (Minimum Viable)

```json
{
  "version": "1",
  "entry": "ingest",
  "nodes": [
    { "id": "ingest", "type": "tool", "name": "FetchDocs", "config": {"url": "https://…"} },
    { "id": "summarize", "type": "llm", "name": "Summarize", "config": {"provider": "openai", "model": "gpt-4o-mini", "system": "Be concise"}, "inputs": {"text": "{{node.ingest.output.content}}"} },
    { "id": "decide", "type": "router", "name": "Decider", "config": {"rule": "len(text)>2000 ? 'deep' : 'shallow'"}, "inputs": {"text": "{{node.summarize.output}}"} },
    { "id": "deep", "type": "llm", "name": "DeepAnalysis", "config": {"provider": "anthropic", "model": "claude-3.5-sonnet"}, "inputs": {"text": "{{node.summarize.output}}"} }
  ],
  "edges": [
    { "from": "ingest", "to": "summarize" },
    { "from": "summarize", "to": "decide" },
    { "from": "decide", "to": "deep", "when": "branch=='deep'" }
  ],
  "limits": { "maxNodes": 20, "maxTokens": 150000, "timeoutSeconds": 120 }
}
```

**Templating:** `{{node.<id>.output}}` for bindings. Router sets `branch`.

---

## 4) Data Model (Postgres)

* **workflows** — `id, owner_id, name, description, graph_json, created_at, updated_at`
* **workflow_runs** — `id, workflow_id, triggered_by, status{queued|running|succeeded|failed|canceled}, started_at, finished_at, total_tokens, total_cost_cents, total_latency_ms, error_summary`
* **run_steps** — `id, run_id, node_id, node_type{llm|tool|router}, status, started_at, finished_at, latency_ms, tokens_input, tokens_output, cost_cents, error`
* **trace_events** — `id, run_id, step_id?, ts, kind{log|llm.request|llm.response|tool.request|tool.response|retry|cache.hit}, payload(jsonb)`
* **provider_bindings** — `id, owner_id, workflow_id, provider, model, temperature`
* **semantic_cache (optional later)** — `key_hash, response, tokens, cost_cents, created_at` (+ `embedding` if pgvector).

---

## 5) API Spec (names + minimal payloads)

* `POST /api/workflows` — `{name, description?, graph_json}` → `{id}`
* `GET  /api/workflows` — list
* `GET  /api/workflows/:id` — get
* `PUT  /api/workflows/:id` — `{name?, description?, graph_json?}`
* `DELETE /api/workflows/:id`
* `POST /api/workflows/:id/runs` — `{input_vars?}` → `{runId}`
* `GET  /api/runs/:runId` — run summary/status
* `GET  /api/runs/:runId/trace` — paginated events
* `GET  /api/runs/:runId/stream` — **SSE** live feed
* `POST /api/runs/:runId/cancel` — cancel

**SSE event**: `event: trace`  `data: { ts, kind, step_id, payload }`

---

## 6) System Diagram (text)

Browser (Next.js) ⇄ API (FastAPI)
→ Enqueue job (Redis) → Worker executes (LangGraph)
→ Write steps + events (Postgres) → Publish events (Redis pubsub)
→ API streams per‑run SSE back to Browser.

---

## 7) Demo Script (2 minutes)

1. Open 4‑node workflow; quick tour of nodes and rules.
2. Click **Run** → live SSE timeline appears.
3. Open a step → show prompt/response, tokens, cost, latency.
4. Force an error → retry shows; fallback provider succeeds.
5. Re‑run same input → `cache.hit` event; cost ≈ 0; show totals.

---

## 8) Build Plan → Tasks (Balanced V1)

**Phase 0 — Prep (½ day)**

* Mono‑repo scaffolding, envs, logging, health/version endpoints, migrations tool.

**Phase 1 — Data Layer (1 day)**

* Create tables; seed demo workflow.

**Phase 2 — Executor Core (2 days)**

* JSON schema; compiler (DAG); sequential executor; retries; totals.

**Phase 3 — Tracing & Streaming (1.5 days)**

* Wrap calls with trace events; persist; SSE endpoint.

**Phase 4 — Frontend Basics (1.5 days)**

* Workflow list; editor (React Flow); save/load; trigger run.

**Phase 5 — Trace Viewer (1.5 days)**

* Live timeline; step detail; run summary header.

**Phase 6 — Fallbacks & Cache & Router (2 days)**

* Pricing map + fallback logic; exact‑match cache; simple router.

**Phase 7 — Guardrails & Polish (1 day)**

* Limits, error surfaces, empty states; two seeded demo flows; README; record demo.

---

## 9) Success Metrics (V1)

* Cache hit rate: **≥30%** for repeated inputs.
* Cost reduction from cache: **40–75%** on repeats.
* p95 step latency visible and accurate; totals correct within **±1%**.
* Run success rate (with retries/fallbacks): **≥95%** on demo flows.
* Demo time: **≤2 minutes** end‑to‑end.

---

## 10) Future Upgrades & Scaling Roadmap

**A. Depth (make V1 stronger)**

* **Semantic Cache** — Embedding‑based similarity; partial‑context reuse; per‑node TTLs.
* **Human‑in‑the‑Loop** — Approval nodes; pause/resume; annotation capture.
* **Advanced Router** — Expression language, metrics‑based routing, canary branching.
* **Parallelism at Scale** — Work‑stealing workers; per‑node concurrency caps; distributed runs.
* **Observability++** — OpenTelemetry traces; span correlation; run diffs; flame‑graph‑like view.
* **Cost Controls** — Per‑workflow budgets, soft/hard stops, alerts, per‑provider quotas.

**B. Breadth (new capabilities)**

* **Template Gallery** — Versioned workflow templates; import/export.
* **A/B Testing Suite** — Traffic splits per node; stats (Bayesian/Chi‑square); winner auto‑promote.
* **Providers Matrix** — Multi‑LLM registry (OpenAI/Anthropic/Cohere/Local); model benchmarks.
* **Knowledge Connectors** — Vectorize from URLs/S3/Slack/Notion; chunking policies; governance.
* **Eval Harness** — Golden sets; automatic regression alerts; quality vs. cost dashboards.
* **Plugins/Tools SDK** — Tool interface + registry; safe sandboxes; permissions.

**C. Productization**

* **Teams & RBAC** — Projects, roles, audit logs, API tokens.
* **Usage/Billing** — Credits, metering, invoices; bring‑your‑own‑key vs. platform‑billed.
* **On‑Prem Mode** — Helm chart; S3/Postgres pluggable; air‑gapped support.

**D. Scale & Reliability**

* **Queues** — Kafka/NATS for high‑throughput runs; exactly‑once step commits.
* **Storage** — Cold storage of traces; compression; partitioning; retention policies.
* **SLA** — Circuit breakers, hedged requests, dead‑letter queues, replay runs.

**E. AI Advancements**

* **Toolformer‑style Planning** — Self‑refining graphs; auto‑generated subgraphs with constraints.
* **Memory Systems** — Short‑/long‑term, episodic memory; retrieval policies.
* **Guardrails** — Safety filters, PII scrubbing, red‑team prompts; hallucination detection.

**Roadmap cadence**

* **Month 1:** Hardening V1 + semantic cache + HITL node.
* **Month 2:** Evals + A/B suite + provider matrix.
* **Month 3:** Teams/RBAC + billing + on‑prem installer.

---

## 11) Task List (Copy‑paste for Linear/Notion)

Use these as tickets. Each includes **Acceptance Criteria (AC)** and **Estimate (Est.)**.

### Phase 0 — Prep

1. **Repo & Mono‑repo Scaffolding**
   AC: `frontend/` + `backend/` folders, root README, `.editorconfig`, `.gitignore`.
   Est.: 0.25d
2. **Env & Secrets Setup**
   AC: `.env.example` with placeholders; documented required vars.
   Est.: 0.25d
3. **Health & Version Endpoints**
   AC: `/health` returns OK; `/version` returns git sha.
   Est.: 0.25d
4. **Migrations Tooling**
   AC: Migration CLI installed; empty initial migration committed.
   Est.: 0.25d

### Phase 1 — Data Layer

5. **Create Core Tables**
   AC: `workflows, workflow_runs, run_steps, trace_events, provider_bindings` created; indexes on `run_id`, `workflow_id`.
   Est.: 0.5d
6. **Seed Demo Workflow**
   AC: One simple 4‑node workflow row exists; loadable via API.
   Est.: 0.25d

### Phase 2 — Executor Core

7. **Workflow JSON Schema Validation**
   AC: Rejects invalid nodes/edges; limits enforced.
   Est.: 0.5d
8. **Graph Compiler (DAG)**
   AC: Topological order computed; cycles rejected with clear error.
   Est.: 0.5d
9. **Sequential Executor**
   AC: Executes nodes in order; records start/end/status.
   Est.: 0.75d
10. **Retry w/ Backoff**
    AC: Transient failures auto‑retry (configurable attempts); logged as `retry`.
    Est.: 0.25d
11. **Usage & Cost Roll‑up**
    AC: Token counts and cost per step and per run computed via pricing map.
    Est.: 0.5d

### Phase 3 — Tracing & Streaming

12. **Trace Events Emitter**
    AC: Emits `llm.request/response`, `tool.request/response`, `log`.
    Est.: 0.5d
13. **Persist Trace Events**
    AC: Events saved to DB with timestamps and step linkage.
    Est.: 0.25d
14. **SSE Run Stream**
    AC: `/api/runs/:id/stream` pushes new events in real time.
    Est.: 0.5d

### Phase 4 — Frontend Basics

15. **Workflow List Page**
    AC: View, create, delete; links to Editor and Runs.
    Est.: 0.5d
16. **Workflow Editor (React Flow)**
    AC: Add/remove nodes, connect edges, edit config; save to API.
    Est.: 1.0d
17. **Trigger Run**
    AC: “Run” button hits API; navigates to live run view.
    Est.: 0.25d

### Phase 5 — Trace Viewer

18. **Timeline Pane**
    AC: Step list with status chips; auto‑scrolls on live updates.
    Est.: 0.5d
19. **Step Detail Pane**
    AC: Inputs, outputs, tokens, cost, latency; raw JSON tab.
    Est.: 0.75d
20. **Run Summary Header**
    AC: Totals and status; elapsed time.
    Est.: 0.25d

### Phase 6 — Fallbacks, Cache, Router

21. **Provider Pricing Map**
    AC: Static pricing for selected models; used in cost calc.
    Est.: 0.25d
22. **Provider Fallback**
    AC: On error/timeout, calls secondary provider; event logged.
    Est.: 0.5d
23. **Exact‑Match Cache**
    AC: Hash key; hit short‑circuits; `cache.hit` event emitted.
    Est.: 0.5d
24. **Simple Router Node**
    AC: Boolean/branch rule gates edges; `branch` visible in events.
    Est.: 0.5d

### Phase 7 — Guardrails & Polish

25. **Limits & Caps**
    AC: Max nodes/tokens/duration enforced with clear errors.
    Est.: 0.25d
26. **Empty/Loading/Error States**
    AC: UX clean for lists, editor, and runs.
    Est.: 0.25d
27. **Seed Two Demo Workflows**
    AC: “Research→Summarize→Decide→Deep” and “CSV→Analysis→Write‑up.”
    Est.: 0.25d
28. **README + Demo Recording**
    AC: 2‑min Loom; repo README with setup, architecture, and demo link.
    Est.: 0.5d

---

## 12) Success Criteria Checklist

* Live trace works and is stable.
* Step details show inputs/outputs/tokens/cost/latency.
* Fallbacks trigger correctly and are visible.
* Cache hits are logged and reduce cost/time measurably.
* Router node branches as expected.
* Demo flows run reliably end‑to‑end.

---

