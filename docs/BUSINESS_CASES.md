# Business problems and implementation choices

## Investment risk monitoring

**User need.** A risk analyst needs consistent checks over a dated position snapshot, both for daily runs and for historical review. Different rule families depend on different dimensions, thresholds and reference data.

**Engineering response.** The runner selects a rule and dimension, checks snapshot availability, obtains data through a DAO, executes the rule and persists the result. Historical replay reuses the dated execution path. Scheduled execution acquires a lease to reduce duplicate runs across instances.

**A failure that matters.** A batch can finish iterating while one rule has failed. Treating iteration completion as business success would hide the missing result. The runner regression test checks that a failed monitor remains a failure in the aggregate. The pure limit example also rejects missing or non-finite values instead of interpreting them as a safe zero position.

**Boundary.** Policy defaults and sample holdings are synthetic. Domain formulas and integration paths need validation against the intended business definitions before operational use.

## Wealth research

**User need.** A fund query may contain an incomplete name, multiple share classes, a request to compare products, or a metric whose history is unavailable. Returning a fluent answer is insufficient if the underlying entities and periods are wrong.

**Engineering response.** The source separates entity recognition and lookup from specialist fund, manager and company tools. Lookups use bounded concurrency. The synthetic data-tool example makes ambiguous matches and partial results explicit, preserves missing history and supplies a deterministic tie-break order.

**A failure that matters.** A new fund has no one-year return. Replacing the missing value with zero misrepresents the observation. The synthetic test checks that the value stays missing. The separate coverage catalog records broader scenario intentions without exposing production evidence or presenting unmeasured accuracy.

**Boundary.** Synthetic tool tests do not establish LLM quality, retrieval recall or the correctness of the external data APIs.

## Business analytics

**User need.** A manager wants to understand branch revenue, its share of a total and changes over time. The answer depends on the observational grain, the relevant period and a valid comparison baseline.

**Engineering response.** The application keeps branch lookup, metric tools, isolated calculations and report requests distinct. Its offline branch/year calculation rejects duplicate observations and leaves growth undefined when the prior-period denominator is missing or zero.

**Public full-stack path.** A newly built synthetic browser demo lets a reviewer choose a year and branch. A local HTTP endpoint queries SQLite using bound parameters and passes records to the same deterministic metric calculation. The browser shows the annual total, each branch's share and an explicit missing-baseline state. This demonstrates the UI/API/SQL contract independently of the private data and model services.

**A failure that matters.** Summing duplicated branch/year rows inflates both the branch result and the company total. The tests reject that input rather than producing a plausible but incorrect chart or summary.

**Boundary.** The local browser UI is a portfolio reconstruction, not original supplied frontend code. The agent's live customer-data path is not connected to the synthetic demo. The report tool returns a descriptor; no local Word/PDF generator is provided.

## Scheduled-job coordination

**User need.** Multiple service instances can trigger the same scheduled task. A process-local scheduler limit cannot coordinate separate instances.

**Engineering response.** A shared database row arbitrates lease acquisition. A random owner token ensures that an expired worker cannot release a newer worker's lease. Tests demonstrate the expiry and takeover sequence using independent connections.

**A failure that matters.** Worker A pauses, its lease expires, and worker B acquires the job. Worker A's later release must leave B's ownership intact. The test checks that sequence directly.

**Boundary.** Lease ownership protects coordination, not every downstream side effect. Idempotent writes and fencing may still be necessary.
