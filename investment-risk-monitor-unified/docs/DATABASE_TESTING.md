# Database integration verification

The integration suite uses the actual connection pools, query adapters, configuration importer, result upsert, ratio monitor and lease implementation. It requires a fresh disposable database whose name ends in `_test`. It creates schema and deletes test rows; never point it at an existing application database.

## Local reproduction

```bash
python -m pip install -r requirements.txt -r requirements-import.txt
docker compose -f compose.integration.yml up -d --wait
export RUN_DB_INTEGRATION=1 DB_HOST=127.0.0.1 DB_NAME=risk_monitor_test
export DB_USER=demo_user DB_PASSWORD=local_test_only
DB_TYPE=mysql DB_PORT=13306 python -m unittest discover -s integration_tests -v
DB_TYPE=pg DB_PORT=15432 python -m unittest discover -s integration_tests -v
python -m unittest discover -s adapter_tests -v
docker compose -f compose.integration.yml down
```

The Compose services use temporary storage and loopback ports. The credentials are non-production examples used only in disposable containers. Recreate the containers before rerunning the integration suite: initialization deliberately does not drop existing tables.

`.github/workflows/database.yml` runs the suite against MySQL 8.4 and PostgreSQL 16, using fresh GitHub Actions services. The workflow is a runnable test definition, not evidence of a successful run until Actions reports success for its commit.

## Coverage

Seven integration tests cover:

1. Idempotent configuration imports and unknown rule references.
2. Transaction rollback and connection-pool reuse.
3. Concurrent lease acquisition, renewal, expiry and stale release rejection.
4. Result upsert and persistence of missing-data results.
5. Classification mapping duplicates, absolute denominator and monitor-to-result persistence.
6. An actual database constraint failure after a partial batch, requiring full rollback.
7. Account yield aggregation and financial versus comprehensive earnings fields.

Five adapter tests load application modules with mocked data access and exercise SQL argument binding, ratio caller contracts, whitelist matching, XLSX reading/formula rejection, and account-scope configuration. They do not prove database behavior.

## Schema scope and limitations

`sql/postgres_init.sql` provides the configuration, result and position tables. It does not make every inherited MySQL-specific domain query portable. `sql/asset_position_tree_mysql.sql` (MySQL) and `sql/asset_position_tree.sql` (PostgreSQL) define the minimal classification mapping required by the adapted queries. Reference-data vendor tables are not supplied.

Lease ownership still depends on application clocks. Renewal failure cannot cancel an in-flight business write. Use idempotent writes and, for stronger guarantees, fencing tokens. The tests do not claim exactly-once execution or coverage of every production failure mode.

On September 28, 2026, [GitHub Actions run 36399446146](https://github.com/PuweiHe/financial-software-engineering/actions/runs/36399446146) passed on MySQL 8.4 and PostgreSQL 16 at commit `eed9e7c`. Each backend executed all seven integration tests and five adapter tests. The development machine had no database/container runtime, so real-server verification was performed in CI. Standard-library and adapter tests also passed locally.

The MySQL mapping schema explicitly matches the snapshot table’s `utf8mb4_unicode_ci` collation. MySQL 8 defaults can otherwise produce an illegal mix of collations in classification joins. The end-to-end ratio test covers this join.
