# Sanitization and verification record

Prepared on 2026-09-28. Scope: four independent portfolio directories in this workspace.

## Processing decisions

- Kept the two risk-monitor variants as one compatible reconstruction; kept the wealth assistant, business analytics assistant and standalone mutex example separate.
- Replaced original environment configuration with empty environment-variable examples. Removed original credentials, hosts, organization labels, author markers and private deployment references.
- Removed deployment-specific Python comments and docstrings where needed; replaced agent prompts with generalized instructions. Replaced remaining risk-policy numeric defaults with synthetic examples. Generic calculations, schemas and tool structures remain.
- Excluded all original logs, spreadsheet/CSV exports, screenshots, binary dictionaries, production question batches and source Git history.
- Reconstructed the 108-case diagnostic package as generic coverage labels only; added 12 new synthetic cases without original questions, answers, traces, accuracy or latency values.
- Removed payload logging and private audit-service writes from the agent copies. External agent integrations and history persistence are disabled by default. Enabled history has a one-hour expiry.

## Verification performed

| Repository | Unit-test methods | Additional exercise |
| --- | ---: | --- |
| investment-risk-monitor-unified | 7 | Offline example shares the calculation used by the demo database monitor |
| wealth-agent | 6 | One test method executes 12 synthetic data-tool cases |
| business-analytics-agent | 7 | Synthetic totals, shares, growth and invalid input cases |
| database-job-mutex | 2 | SQLite lease exclusion and stale release through independent connections |

All 22 methods passed. All four offline demos completed successfully. Python sources were parsed for syntax. Each repository's privacy-pattern check reported zero findings. A separate local comparison against original configuration secrets, private IPs, email addresses, token candidates and organization/author markers found no matches in the output repositories; no source-derived lookup list is stored in the deliverables.

## What remains unverified

Live database services, LLM calls, customer data APIs, Redis, speech, code sandbox and object storage were not exercised. Inherited dependency lists were not installed or freshly resolved. The standalone SQLite mutex demo is not a MySQL concurrency test. No claim is made about complete business-rule correctness, production performance, or legal publication rights. Automated pattern checks cannot prove the absence of every possible identifying detail.

This record describes the preparation stage before the initial GitHub release. Later work added targeted MySQL/PostgreSQL integration checks and a synthetic full-stack operations demo; their current coverage is documented in `docs/VERIFICATION.md`. Original inputs remain outside these output directories.
