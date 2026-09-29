# Engineering audit and implementation plan

Baseline: `4a624d2`. The repository contains four independent Python applications in 227 tracked files. Review covers source/configuration inventories, syntax and call-site inspection, existing tests, and execution tracing of the browser metrics path, both conversation endpoints, tool adapters, risk runner, DAO/persistence and scheduled leases. Proprietary services and production financial formulas cannot be validated from this public copy.

## Product and execution paths

- Branch managers select a year/branch in the browser. A local HTTP handler queries SQLite and calls a deterministic metric calculation; the browser renders totals, shares and missing baselines. The separate operations agent routes conversational requests to branch, metrics, calculation and report tools.
- Research users ask about funds, managers or companies. A model extracts names, data APIs resolve candidates, and a supervisor invokes specialist tools. FastAPI exposes streaming and non-streaming responses. Optional Redis retains conversation history.
- Risk analysts run configured rules over dated holdings. DAO queries feed rule calculations and database result upserts. A scheduler uses a renewable database lease; historical replay reuses the dated runner. The independent mutex project isolates ownership/expiry behavior.
- External integrations include model/data HTTP APIs, Redis, optional E2B/object storage and speech. They are disabled by default. There is no local identity provider or production authorization implementation.

## Findings before changes

| ID / priority | Affected files | Current problem | Proposed change and engineering justification | Recruiting value | Risk |
| --- | --- | --- | --- | --- | --- |
| S1 / P0 when external data is enabled | `investment-risk-monitor-unified/dao/*.py` | Dates, dimensions and security codes are interpolated into SQL. Values from configuration/source data can change SQL structure. | Bind every dynamic value, including IN lists; handle empty lists explicitly. Test quotes and adversarial strings through actual DAO methods. | SQL correctness and security beyond a demo query. | Medium: preserve placeholder order and existing domain semantics. |
| A1 / P1 | Both agents' `util/yield_util.py` | Card payloads are discarded into `{}`; model text containing protocol-like keys is parsed as an event. | Keep text opaque; serialize explicit event envelopes with real card data. | A testable UI/backend event contract. | Low: restores intended card behavior. |
| A2 / P1 | Operations `agent/mutil_agent.py`, `web/agent_api.py` | Non-streaming path invokes async-only specialist tools synchronously; streaming failures can end without reporting an error; cancellation is swallowed. | Use async invocation, bounded execution, explicit error events and cancellation propagation. | Reliable agent orchestration and API behavior. | Medium: exercise real orchestration with fake model/tool events. |
| A3 / P1 | Agent card/history/request utilities | Global card registries are keyed by client-supplied request IDs. Same-ID concurrent requests can mix cards; IDs have no size/shape limits. | Store cards in request-local context, reset it in all exits, validate request inputs and namespace history safely. | Concurrency and request isolation. | Medium: validate parallel requests and failure cleanup. |
| A4 / P1 | Wealth entity recognition and both HTTP utilities | Regex extracts partial JSON; malformed/oversized entities are not validated; upstream errors become empty data. | Strict extraction schema, bounded candidate count, explicit transport errors, status checks and timeouts. | Deterministic boundaries around probabilistic output. | Medium: old private adapters may need contract changes. |
| A5 / P1 | Operations sandbox, speech service | Code execution/storage is enabled by a broad external-services flag; optional speech uses an async event in a synchronous worker and can hang. | Require a separate execution opt-in; bound code/audio and execution time; repair speech completion/cleanup. | Side-effect and resource boundaries. | Medium: external SDK/service tests remain separate. |
| R1 / P1 | Risk `monitors/monitor_runner.py` | Single-monitor execution across dimensions returns only the last result, hiding earlier failures. | Aggregate multi-dimension status/results; preserve single-dimension response. | Business status correctness. | Low: regression test mixed outcomes. |
| F1 / P1 | `business-analytics-agent/demo.py`, `portfolio_demo/*` | Weak numeric input validation; failed requests can leave stale values under new controls; UI has no behavior tests. | Validate records, clear stale reports, add retry and deterministic browser tests. | Defensible end-to-end behavior. | Low. |
| E1 / P2 | Agent tests and `wealth-agent/evals/` | Offline data examples do not exercise API/agent execution. The 108-label catalog is not a model evaluation. | Add dependency-backed API/orchestration tests and a small recorded-output contract evaluation, labeled separately from live model quality. | Evidence for agent engineering without fabricated accuracy. | Low to medium. |
| D1 / P2 | Manifests, CI, docs | Inherited dependency sets are not resolved here; CI omits agent-service imports, frontend behavior, lint and type checks. | Resolve a reproducible service test environment; add focused lint/type/format gates, frontend checks and dependency-backed service tests. | Clone-to-check reproducibility. | Medium: avoid claiming whole-tree strict typing. |
| P1 / P3 | Agent utility code and recruiter docs | Generic log messages, no-op audit scaffolding, outdated counts and dead helpers obscure core workflows. | Remove unused scaffolding, use safe error metadata, and document tested boundaries and tradeoffs. | Faster code review, less generated-looking noise. | Low: confirm call sites first. |

P0 describes an exploitable code pattern when configured with external data, not evidence that a public deployment has been compromised. The initial privacy scan reports no matching credentials; pattern scanning is not a full secret-history audit.

## Ordered implementation

1. Establish the unchanged baseline and isolated service dependencies; capture defects with behavior tests.
2. Bind DAO values and correct aggregate risk results; verify query boundaries and the existing risk suite.
3. Fix event serialization, request-local cards, non-streaming async execution, cancellation and execution budgets. Test the real service boundary with injected model behavior.
4. Validate entity extraction and transport responses. Add bounded optional execution/speech behavior and contract evaluations.
5. Strengthen metrics validation and browser failure/retry states; test the API and browser-facing code.
6. Add focused quality/CI gates, update architecture/setup/reviewer documentation, and run a final regression and diff review.

## Deliberate scope

Keep the four independent application boundaries. Adding a queue, Kubernetes, a shared microservice framework or a new frontend framework would not solve the observed defects. Local demos remain local synthetic applications; authenticated customer deployments still require a trusted identity and record-level authorization boundary. Full legacy financial-rule certification, live provider quality/latency measurements, and distributed fencing require data/infrastructure not included here and must remain explicit integration work.

## Additional confirmed finding during implementation

The shared query adapter duplicated DB-API operations and inserted a batch one row/transaction at a time, risking partial writes and mismatched dictionary-column order. This P1 finding affected `db/query_adapter.py`. The fix uses stable columns and a single pooled transaction, preserving public helper names. Three SQLite-backed regression tests check ordering, full rollback and identifier/shape rejection. The risk is medium because real MySQL/PostgreSQL execution must also pass CI.

Implementation results and remaining work are recorded in [the final review](ENGINEERING_REVIEW.md) and [verification scope](VERIFICATION.md).
