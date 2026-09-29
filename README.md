# Financial Software Engineering Portfolio

[![Offline checks](https://github.com/PuweiHe/financial-software-engineering/actions/workflows/portfolio.yml/badge.svg)](https://github.com/PuweiHe/financial-software-engineering/actions/workflows/portfolio.yml) [![Database integration checks](https://github.com/PuweiHe/financial-software-engineering/actions/workflows/database.yml/badge.svg)](https://github.com/PuweiHe/financial-software-engineering/actions/workflows/database.yml)

I worked across frontend development, Python backend services, SQL, and agent applications while translating financial institutions' business requirements into software. This repository presents generalized, synthetic reconstructions of representative internship workflows. It is designed to let a reviewer inspect the business problem, follow the implementation, and run the evidence without access to a customer's systems.

**Review in five minutes:** [run the full-stack branch analytics demo](business-analytics-agent/README.md#try-the-full-stack-business-scenario), then follow the [code review guide](docs/REVIEW_GUIDE.md) from a business request through the UI, API, SQL, agent routing, and focused tests. The runnable browser path and the retained LLM agent services have different verification scopes; the guide identifies both.

## Start with a working product path

**Business scenario:** an operations manager asks which branches contributed to annual revenue and how each branch changed from the prior year. The [Business Analytics Agent](business-analytics-agent/) contains the domain agent and API adapters. Its new [browser demo](business-analytics-agent/portfolio_demo/) gives that question a complete local path: browser controls → HTTP API → parameterized SQLite query → deterministic metric calculation → visible results. The demo uses synthetic branch records and does not invoke an LLM.

```bash
cd business-analytics-agent
python3 -m portfolio_demo.server
# Open http://127.0.0.1:8765/
```

Choose 2025 and `BRANCH003`: the sample branch contributes 20% of annual revenue, while its growth reads **No baseline** because no 2024 record exists. The distinction prevents missing history from becoming a misleading zero.

## Projects by engineering focus

| Project | Concrete business problem | Inspectable engineering evidence |
| --- | --- | --- |
| [Business Analytics Agent](business-analytics-agent/) | Branch managers need consistent revenue, share, growth, and report requests from conversational workflows. | [Full-stack local demo](business-analytics-agent/portfolio_demo/), [metric tests](business-analytics-agent/tests/test_demo.py), FastAPI/SSE and specialist tools. |
| [Investment Risk Monitor](investment-risk-monitor-unified/) | Risk analysts must evaluate dated holdings, preserve missing-data signals, and replay historical checks. | [Configuration-to-result workflow](investment-risk-monitor-unified/docs/CONFIGURATION_WORKFLOW.md), [MySQL/PostgreSQL integration tests](investment-risk-monitor-unified/integration_tests/test_database.py), transactional imports and distributed leases. |
| [Wealth Research Agent](wealth-agent/) | Research requests may match multiple funds or lack a requested return history. | [Entity resolution](wealth-agent/agent/entity_recognizer.py), specialist tool routing, bounded lookups, [synthetic cases](wealth-agent/evals/synthetic_cases.json), FastAPI/SSE. |
| [Database Job Mutex](database-job-mutex/) | More than one application instance may start the same scheduled task. | Owner-token lease, conditional SQL acquisition, and [stale-release tests](database-job-mutex/tests/test_lease.py). |

**For SDE/SWE review:** run the browser demo, then inspect the risk monitor's database tests and the mutex's concurrency case. **For agent engineering review:** inspect the two domain agent architectures after the runnable examples; their live model and customer-data adapters require external services.

## My role and the public reconstruction

My internship work included working with financial-institution stakeholders to clarify business needs, implementing frontend and backend functionality, writing SQL to support data-driven requirements, and developing agent features for domain workflows. The projects here illustrate those areas through branch analytics, investment-risk monitoring, and wealth research. [Contribution and scope notes](docs/CONTRIBUTIONS.md) distinguish this stated role from functionality added for the public portfolio; they do not attribute every retained line of a team codebase to one person.

The public repository adds synthetic fixtures, local demos, tests, and privacy changes so a reviewer can run meaningful paths. The business-analytics browser UI is a new portfolio reconstruction; frontend source from the original operations project was not present in the supplied files.

## Reproduce the checks

```bash
git clone https://github.com/PuweiHe/financial-software-engineering.git
cd financial-software-engineering
python3 scripts/check_all.py
```

The offline runner uses Python 3.11+ with no paid model, credentials, or database server. It runs privacy/syntax checks, unit tests, and four synthetic demos in separate project processes. The browser demo needs only Python's standard library. The separate database workflow runs the risk-monitor integration suite on MySQL 8.4 and PostgreSQL 16. See [verification scope](docs/VERIFICATION.md) for exactly what each check proves.

The repository-wide publishable-tree check also rejects common credential formats, personal paths, nonlocal IP addresses, and hardcoded numeric user IDs in Python adapter fields. It reports file paths and categories without printing matched values.

## Business decisions visible in code

| Requirement | Engineering choice | Evidence |
| --- | --- | --- |
| A branch's missing prior year must not read as zero growth. | Preserve an undefined growth value through SQL, API, and browser presentation. | [Metric implementation](business-analytics-agent/demo.py), [HTTP checks](business-analytics-agent/tests/test_portfolio_demo.py) |
| An absent risk position must not read as a safe zero exposure. | Emit a data-quality result with a null indicator and an explicit status. | [Ratio evaluator](investment-risk-monitor-unified/core/holding_ratio.py), [database check](investment-risk-monitor-unified/integration_tests/test_database.py) |
| A batch must report failed rules even after it finishes iterating. | Aggregate execution status at the runner boundary. | [Runner regression test](investment-risk-monitor-unified/tests/test_runner_contract.py) |
| A stale worker must not release a successor's lease. | Require the owner token for release. | [Lease implementation](investment-risk-monitor-unified/utils/distributed_lock.py), [concurrency test](investment-risk-monitor-unified/integration_tests/test_database.py) |
| A fund name can be ambiguous or lack one-year history. | Separate entity lookup and specialist tools; retain ambiguity and missing values. | [Fund cases](wealth-agent/evals/synthetic_cases.json), [tool tests](wealth-agent/tests/test_demo.py) |

Read the [business case studies](docs/BUSINESS_CASES.md) and [architecture decisions](docs/ARCHITECTURE.md) for context. All public data is synthetic. No customer records, credentials, production results, or measured business impact are claimed.
