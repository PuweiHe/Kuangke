# Database Job Mutex

A small standalone database-lease example for scheduled jobs. It is useful independently of the investment monitoring application, so it remains a separate portfolio repository.

`distributed_mutex_job.py` retains the MySQL implementation: a conditional database update acquires the lease, a random owner token protects release, and the scheduler records execution events. `distributed_mutex.sql` contains the schema. Connection settings are environment-driven.

## Offline demonstration

```bash
python demo.py
python -m unittest discover -s tests -v
python scripts/check_privacy.py
```

The standard-library SQLite demonstration tests the same lease concepts through two independent connections, including lease expiry and rejection of stale release. It does not verify MySQL locking or scheduler behavior.

## MySQL integration

Install `requirements.txt`, copy `.env.example` to `.env` and configure an empty local database. Apply `distributed_mutex.sql`, or explicitly set `INIT_SCHEMA=true` for initialization. Use `RUN_ONCE=true` for one run and `RUN_ONCE=false` to start the scheduler. Run `python distributed_mutex_job.py`. The business callback is an extension point and intentionally performs no business work.

This implementation has no heartbeat renewal. A job that outlives its lease can overlap a successor, and owner-checked release does not prevent stale writes. Set an appropriate lease and make downstream writes idempotent; stricter systems need fencing. The investment-monitor project has a separate adapter with heartbeat renewal. MySQL integration has not been exercised here.
