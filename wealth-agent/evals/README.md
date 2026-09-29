# Synthetic evaluation examples

`coverage_catalog.json` retains 108 generic module and intent labels from a larger diagnostic collection. Original questions, names, product identifiers, replies, expected answers, timestamps, accuracy scores, latencies, API traces, prompts, and evidence were deliberately excluded. The catalog is a coverage design, not 108 executed tests.

`synthetic_cases.json` contains 12 newly authored executable examples against `demo.execute`. They exercise deterministic data tools, not the language model or the original system. Run `python -m unittest discover -s tests -v` from the repository root. No original performance or accuracy results are claimed.
