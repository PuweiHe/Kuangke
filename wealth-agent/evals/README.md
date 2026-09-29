# Synthetic evaluation examples

`coverage_catalog.json` retains 108 generic module and intent labels from a larger diagnostic collection. Original questions, names, product identifiers, replies, expected answers, timestamps, accuracy scores, latencies, API traces, prompts, and evidence were deliberately excluded. The catalog is a coverage design, not 108 executed tests.

`synthetic_cases.json` contains 12 newly authored executable examples against `demo.execute`. They exercise deterministic data tools, not the language model or the original system. Run `python -m unittest discover -s tests -v` from the wealth-agent directory. No original performance or accuracy results are claimed.

## Extraction output contracts

`extraction_contracts.json` contains eight synthetic recorded outputs: valid, deduplicated and empty names, wrong types, blank values, excessive fan-out and unexpected fields. After installing service dependencies, run `python evals/evaluate_contracts.py`. The harness uses the same Pydantic schema as the live extraction path and exits nonzero on a mismatched expectation.

This evaluates deterministic acceptance/rejection of model-shaped output. It does not call a model or measure entity extraction accuracy, grounding, latency or cost. Those need separate representative labeled questions and a configured provider.
