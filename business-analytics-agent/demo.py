"""Synthetic CLI example; the same calculation serves the browser API."""
import json
from pathlib import Path
from metrics import summarize

if __name__ == '__main__':
    records = json.loads((Path(__file__).parent / 'examples/branches.json').read_text())
    print(json.dumps(summarize(records, 2025), indent=2))
