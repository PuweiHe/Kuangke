"""Deterministic account-level ratio evaluation with explicit missing-data results."""
import json
import math
from collections import defaultdict


def account_scope(scope):
    """An optional JSON array names expected accounts, including absent accounts."""
    if scope is None or scope == '':
        return None
    values = json.loads(scope) if isinstance(scope, str) else scope
    if not isinstance(values, list) or not values or any(not isinstance(x, str) or not x.strip() for x in values):
        raise ValueError('Account scope must be a nonempty JSON array of strings')
    if len(set(values)) != len(values):
        raise ValueError('Account scope contains duplicate accounts')
    return values


def evaluate_ratios(numerator, denominator, threshold, expected=None, repo=None):
    """Aggregate signed numerators; denominator rows must use the chosen SQL basis.

    Missing rows are unknown, not zero. A known zero repo balance makes a
    repo-gated rule not applicable. Unknown/nonfinite balances stay visible.
    """
    threshold = float(threshold)
    if not math.isfinite(threshold) or threshold < 0:
        raise ValueError('Threshold must be finite and nonnegative')
    names = {}
    def aggregate(rows):
        totals = defaultdict(float)
        invalid = set()
        for row in rows:
            key = row.get('ztbh')
            if key is None or not str(key).strip():
                raise ValueError('Missing account identifier')
            key = str(key)
            names[key] = str(row.get('jjztmc') or names.get(key, key))
            try:
                value = float(row['dirty_price_market_value'])
                if not math.isfinite(value):
                    raise ValueError()
                totals[key] += value
                if not math.isfinite(totals[key]):
                    raise ValueError()
            except (KeyError, TypeError, ValueError, OverflowError):
                invalid.add(key)
        return totals, invalid
    num, bad_num = aggregate(numerator)
    den, bad_den = aggregate(denominator)
    rep, bad_rep = aggregate(repo or [])
    accounts = account_scope(expected) if expected is not None else sorted(set(num) | set(den) | bad_num | bad_den | set(rep) | bad_rep)
    results = []
    for key in accounts:
        status, value, reason = 'ok', None, ''
        if repo is not None and (key not in rep or key in bad_rep):
            status, reason = 'missing_data', 'Repo balance is unavailable'
        elif repo is not None and rep[key] == 0:
            status, reason = 'not_applicable', 'Known repo balance is zero'
        elif key not in num or key not in den or key in bad_num or key in bad_den:
            status, reason = 'missing_data', 'Numerator or denominator is unavailable'
        elif den[key] <= 0:
            status, reason = 'invalid_data', 'Denominator must be positive'
        else:
            value = num[key] / den[key]
            if not math.isfinite(value):
                status, value, reason = 'invalid_data', None, 'Ratio is not finite'
            else:
                status = 'breach' if value > threshold else 'ok'
                reason = f'Ratio {value:.6f}; limit {threshold:.6f}'
        level = 2 if status in {'missing_data', 'invalid_data'} else int(status == 'breach')
        results.append(dict(portfolio_code=key, portfolio_name=names.get(key, key),
                            indicator_value=value, alert_level=level,
                            evaluation_status=status, alert_message=f'[{status}] {reason}'))
    return results
