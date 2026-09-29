# Verification scope

Run `python3 scripts/check_all.py` from the repository root. It uses the current Python interpreter, isolates each project in its own process, disables external agent services, and stops on the first failed command.

| Project | Test methods | Coverage represented |
| --- | ---: | --- |
| Risk monitor | 23 | Date ranges, mocked leases, failure aggregation, ratio/yield evaluation, asset normalization and configuration validation |
| Wealth agent | 6 | External-service configuration plus 12 synthetic data-tool cases and invalid/missing-data checks |
| Business analytics agent | 12 | External-service configuration, metric totals, growth, zero denominators, duplicate observations, local HTTP contracts and bound SQL access |
| Database job mutex | 2 | SQLite exclusion, lease expiry/stale release and invalid lease duration |

All four directories also contain a runnable synthetic demo and a privacy-pattern scanner that parses Python source for syntax. The root GitHub Actions workflow runs the checks for each project on Python 3.11 and 3.13. Workflows nested inside project folders are only relevant if a project is later extracted into its own repository.

## Interpretation

- The 43 methods are focused checks, not whole-application coverage.
- The 12 wealth cases are newly authored examples against deterministic data operations, not LLM evaluations.
- The 108-label catalog is a coverage design artifact, not a passed test suite.
- Mocked lease tests and a SQLite example do not validate MySQL/PostgreSQL integration.
- Syntax checks do not resolve or import every third-party dependency.
- Privacy-pattern checks do not prove that every possible identifying detail is absent.

Live model/data APIs, Redis, speech, sandbox and object storage require separate integration work. Database verification is scoped below. No production performance, user count, financial impact or benchmark result is asserted.

## Workflow extension

The risk extension added 16 standard-library tests (23 risk tests) and five separate application-adapter tests. The database workflow has passed seven integration methods plus five adapter methods on each of MySQL 8.4 and PostgreSQL 16. Coverage includes transactional imports, rollback, result upserts, classification mapping, account aggregation and concurrent leases. This does not validate every inherited domain query or external reference-data service.

The business-analytics browser demo adds five focused methods: three exercise the actual local HTTP endpoints and two exercise the SQLite boundary. In environments that prohibit loopback sockets, the HTTP class skips and the repository checks still run. Neither these tests nor the UI represent a live LLM evaluation.
