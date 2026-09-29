"""Validate configuration by default; --apply explicitly enables database writes."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.config_import import ImportValidationError, apply_import, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['rules', 'dimensions', 'assets'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--sheet')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        rows = prepare(args.kind, args.input, args.sheet)
        if args.apply:
            from config.settings import DB_TYPE
            from db.factory import get_pool
            with get_pool().connection() as connection:
                apply_import(connection, DB_TYPE, args.kind, rows)
        print(json.dumps({'kind': args.kind, 'rows': len(rows), 'mode': 'applied' if args.apply else 'dry-run'}))
        return 0
    except ImportValidationError as exc:
        print(json.dumps({'errors': exc.errors}), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': 'Import failed; no raw input or connection details logged'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
