# Investment Risk Monitor (Portfolio Reconstruction)

This repository is a local, generalized reconstruction of two related internship codebases. It keeps the rule-driven monitoring flow from the first codebase and adapts reusable capabilities from the second: historical replay, monitor discovery, missing-source-data detection, result categorization, and a database-backed lease for scheduled runs. It does not represent either customer's deployment.

## What it does

- Loads enabled monitoring rules and dimensions from database tables.
- Runs monitor classes against a dated position snapshot and stores results with an upsert.
- Runs one monitor, a monitor category, a full day, or an inclusive historical date range.
- Uses a database lease to prevent duplicate scheduled runs across instances. A random owner token protects against stale release; a heartbeat renews long-running jobs.
- Can connect through the MySQL or PostgreSQL pool and query adapter. The included domain queries were originally written for MySQL; PostgreSQL support for all domain rules remains unverified.
- Sends email only when notification settings are explicitly enabled.

The demo data and retained policy defaults are synthetic portfolio examples. Organization labels, deployment-specific comments, customer prompts, numeric policy defaults, credentials and private data exports were removed or replaced. Generic domain formulas and architecture remain; synthetic limits must not be treated as investment guidance.

## Offline example

Run `python demo.py`, `python -m unittest discover -s tests -v`, and `python scripts/check_privacy.py`. These commands use only the standard library. The demo uses the same pure limit calculation as the database monitor.

## Local MySQL example

1. Create a Python 3.11 environment and install `requirements.txt`.
2. Copy `.env.example` to `.env`, set local database credentials, and export those variables into the shell. The Python application reads environment variables directly; Docker Compose reads `.env` through `env_file`.
3. Create an empty database named `risk_monitor_demo` (or set `DB_NAME`). Apply, in order, `sql/init.sql`, `sql/position_snapshot.sql`, `sql/mysql_job_lock.sql`, and `examples/demo_seed_mysql.sql`.
4. Run `python main.py --run-now --date 2025-01-02 --monitor DEMO-PL-0001`.
5. Inspect `risk_monitor_result`. The synthetic `P001` portfolio exceeds the example limit and `P002` does not.

To run the scheduler, use `python scheduler.py`. To replay a range, use `python main.py --run-now --start-date 20250101 --end-date 20250131`. The scheduled path requires the lock table; manual runs do not acquire a lease.

## Configuration

Database connection, pool, schedule, optional notifications, and example limits are read from environment variables in `config/settings.py`. `.env.example` contains placeholders only. No credentials or original customer data are included.

`sql/postgres_job_lock.sql` provides the PostgreSQL lease table. The PostgreSQL connection and result upsert paths are present, but the entire domain SQL layer has not been validated against PostgreSQL. The MySQL schema files are not PostgreSQL migrations.

## Verification and limits

Run `python -m unittest discover -s tests -v` for the standard-library tests covering dates, historical replay, lease behavior, ratio and yield evaluation, and configuration validation. The targeted database suite passed on MySQL 8.4 and PostgreSQL 16 in [GitHub Actions](https://github.com/PuweiHe/financial-software-engineering/actions/runs/36399657882); see the exact scope in [Database integration verification](docs/DATABASE_TESTING.md).

A lease reduces duplicate scheduled execution but cannot undo writes if a process loses database connectivity while the job continues. Downstream writes should be idempotent. This is a generalized portfolio reconstruction. The retained domain DAOs also need parameterized SQL and integration testing before production use.

## Configuration ingestion and rule extensions

See [Configuration-to-monitor workflow](docs/CONFIGURATION_WORKFLOW.md) for validated CSV/XLSX imports, explicit account scope, ratio completeness, repo applicability, yield aggregation and security-code matching. Start with a read-only validation:

```bash
python scripts/import_config.py rules examples/config/rules.csv
```

See [Database integration verification](docs/DATABASE_TESTING.md) for disposable MySQL/PostgreSQL services and the real-adapter test suite. These tests require separate dependencies and database services; they are not part of the credential-free demo. Fresh MySQL setups using the adapted financial-product rule also need `sql/asset_position_tree_mysql.sql`. Fresh PostgreSQL setups use `sql/postgres_init.sql`, `sql/postgres_job_lock.sql` and `sql/asset_position_tree.sql`.
