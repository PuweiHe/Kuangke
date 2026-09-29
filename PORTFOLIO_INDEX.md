# Portfolio repository index

This portfolio uses one monorepo. Each directory remains an independently runnable project that can be extracted later. Original folders were left in place; no source Git history, remote, credentials or private data files were imported. The root README is the recruiter-facing entry point.

| Repository directory | Scope | Grouping decision |
| --- | --- | --- |
| `investment-risk-monitor-unified` | Rules, historical replay, source checks, result storage and scheduled leases | The two monitoring versions share the same rule framework; compatible infrastructure features were adapted into one project. |
| `wealth-agent` | Entity resolution and specialist research tools | Generic coverage labels from the 108-case diagnosis package are included in `evals/`; original evidence and responses are excluded. |
| `business-analytics-agent` | Branch lookup, business metrics, calculation and report-request tools; a new synthetic browser/API/SQLite demo | Kept separate because business entities, interfaces and tools differ from wealth research. |
| `database-job-mutex` | Standalone scheduled-job lease example | Kept separate because it is a reusable infrastructure example with its own SQL schema and lifecycle. |

## Material not republished

- The binary third-party data dictionary is excluded, including its embedded content.
- Original operational instructions, private deployment details, credentials and database configuration are excluded; each repository has fresh local setup instructions.
- Source logs, spreadsheets, data exports, screenshots, production questions and answer traces are excluded.
- The diagnostic collection becomes a 108-label coverage catalog plus 12 newly authored synthetic tool cases. It is not represented as a public production benchmark.

## Verification and publishing

From each project directory, run `python scripts/check_privacy.py`, `python -m unittest discover -s tests -v`, and `python demo.py`. Included CI workflows run these offline checks. The operations browser demo runs separately with `python -m portfolio_demo.server`. The risk monitor also has a successful MySQL/PostgreSQL integration workflow; live agent/model integrations remain unverified. See each README for exact scope.

The root CI workflow runs all four projects independently. No license has been assigned to reused internship code; the preparation addresses data exposure and repository packaging, not ownership rights.
