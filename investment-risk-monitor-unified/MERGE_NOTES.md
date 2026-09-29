# Merge notes

The first codebase supplies the monitor classes, DAO structure, runner, notifier, and MySQL/PostgreSQL pool abstraction. The second codebase supplied the design direction for historical replay, dynamic monitor registration, source-data checks, result categories, and scheduled-job coordination.

Adaptations made here:

- Historical replay accepts an inclusive date range and counts a completed day as successful only when its monitors have no reported failures.
- Monitor discovery caches classes, not mutable monitor instances; every execution receives a new instance.
- Both scheduler entry points acquire the same database lease. The lease uses the selected database adapter, owner tokens, and renewal.
- Missing-source-data checks happen once per requested run rather than once per monitor.
- Result persistence uses database-specific upsert syntax and includes a monitor category.
- Configuration is environment-driven; original credentials, hosts, emails, company identifiers, logs, spreadsheets, and data exports are excluded. Remaining numeric policy defaults were replaced with synthetic examples, and deployment-specific rule comments were removed. Generic domain calculations remain.

Client-specific schema rewriting, dimension-map rows, and changed business-rule formulas from the second codebase were not copied. They depended on a particular deployment and could change the first codebase's semantics. The common implementation remains available through the separate original folders outside this new project.
