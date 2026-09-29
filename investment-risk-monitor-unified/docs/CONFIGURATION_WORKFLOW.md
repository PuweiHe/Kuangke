# Configuration-to-monitor workflow

This extension turns a business rule table into validated configuration, database rows and observable monitoring results. All checked-in examples are synthetic. No source workbook, customer account list or original issue log is included.

## Import contract

The three CSV files in `examples/config/` are the canonical templates. An XLSX sheet may use the same exact headers; install `requirements-import.txt` to read it. Identifiers must be text, preserving leading zeroes. Select `--sheet` explicitly for multi-sheet workbooks. Formulas, Excel error cells, duplicate keys, invalid flags, non-finite thresholds and invalid scopes are rejected. The tool reports row/field errors without printing entire input rows.

```bash
python scripts/import_config.py rules examples/config/rules.csv
python scripts/import_config.py dimensions examples/config/dimensions.csv
python scripts/import_config.py assets examples/config/assets.csv
```

These are dry runs and do not load database drivers or connect to a server. Numeric rule thresholds accept decimals or percentages. A blank threshold is rejected; zero is valid. The first template intentionally supports numeric rules only, not every inherited policy type. Compound dimensions must be supplied as separate rows rather than guessing whether an ampersand means a conjunction or a label.

To apply, initialize a disposable database, export the documented DB environment variables, and append `--apply`. Import rules before dimensions. Each file is one transaction, not one transaction across all three files. An unknown rule reference is rejected; any write failure rolls back the entire file. No import operation truncates tables. Natural-key upserts make repeated imports idempotent. The caller must provide an exclusive connection with autocommit disabled.

For an existing MySQL database, inspect duplicate asset keys before applying `sql/add_assets_import_key.sql`. Fresh `sql/init.sql` already includes this index. The importer requires a year; older nullable-year records are outside its managed key contract. This import workflow assumes configuration is managed through these imports; it does not prevent unrelated clients from deleting referenced rules.

## Adapted rules

| Rule | Data contract and behavior | Verification |
| --- | --- | --- |
| IR-RC-0001 / 0002 | Account universe comes from explicit JSON `scope`, otherwise the dated dimension snapshot. Missing numerator/denominator produces a visible data-quality result. | `tests/test_holding_ratio.py`, adapter checks |
| IR-RC-0003 / 0004 | Absolute-value denominator, signed numerator, repo applicability gate. A known zero repo balance yields `not_applicable`; missing repo data is not assumed zero. | Ratio unit cases, database mapping/end-to-end case |
| FY-IO-0001 / 0002 | Explicit JSON account scope required. Aggregate the full account before applying `default_value` as the minimum market value. Financial/comprehensive earnings use separate source fields. | Yield unit cases, database aggregation case |
| BW-IF-0003 | Normalize supported security suffixes and compare to the code field of reference rows. An unavailable whitelist is a data-quality error. | Asset-code unit cases, monitor adapter case |

The ratio query uses `EXISTS` instead of a join so duplicate classification mappings cannot multiply positions. Query values are parameterized. The legacy `mkt_yields` alias was corrected to the calculation contract `dirty_price_market_value`.

`scope` for these account-scoped rules is a JSON array such as `["P001", "P002"]`. Explicit scope can identify entirely missing accounts; snapshot-derived scope cannot know accounts absent from the whole snapshot. Two other inherited account-specific yield rules now also require explicit scope instead of customer-specific defaults; their remaining domain calculations have not been rewritten.

The four holding rules use synthetic fallback thresholds only when configuration is absent. Zero is retained. Yield targets must be configured. Annualization retains the existing simple Actual/365 year-to-date convention; it is not a compounded return. `default_value` is the account minimum in the same units as the stored market value; no production threshold is inferred.

The calculation result exposes `evaluation_status`. To preserve the existing database contract, the status is persisted as a prefix in `alert_message`; no new status column is claimed. `missing_data` and `invalid_data` use alert level 2 and a NULL indicator. `breach` uses level 1; `ok` and `not_applicable` use level 0, with NULL for a not-applicable indicator. Execution `success` means results were saved, not that every portfolio passed its rule.

## Deliberate boundaries

- New regulatory/account-product requirements from source material are not presented as implemented features.
- The wider inherited rule catalog is not fully validated by these targeted tests.
- The reference-data whitelist query retains the configured deployment's existing reference tables; new customer-specific schema rewriting and unverified replacement reference tables were not copied.
- Unused alternative DAO methods, old YAML encryption, duplicate launch scripts and customer question batches were not copied merely to increase feature count.
- Configurations require domain review; no legal/regulatory correctness claim is made from a historical requirements workbook.
