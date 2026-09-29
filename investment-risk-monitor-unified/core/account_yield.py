"""Account yield targets with explicit data quality and applicability states."""
import math
from core.holding_ratio import account_scope
from utils.calc_utils import CalcUtils


def evaluate_account_yields(rows, accounts, target, minimum_value, business_date):
    accounts = account_scope(accounts)
    if accounts is None:
        raise ValueError('Explicit accounts are required')
    target, minimum_value = float(target), float(minimum_value)
    if not math.isfinite(target) or not math.isfinite(minimum_value) or minimum_value < 0:
        raise ValueError('Invalid yield target or minimum value')
    by_code = {}
    for row in rows:
        key = str(row['ztbh'])
        if key in by_code:
            raise ValueError('Duplicate account aggregate')
        by_code[key] = row
    result = []
    for key in accounts:
        row = by_code.get(key, {})
        status, value, message = 'missing_data', None, 'Account yield inputs unavailable'
        try:
            amount = float(row['market_value'])
            earnings = float(row['earnings'])
            capital = float(row['capital'])
            if not all(math.isfinite(x) for x in (amount, earnings, capital)):
                raise ValueError()
            if amount < minimum_value:
                status, message = 'not_applicable', 'Market value below configured minimum'
            elif capital <= 0:
                status, message = 'invalid_data', 'Capital denominator must be positive'
            else:
                value = CalcUtils.annualize(earnings / capital, business_date)
                if not math.isfinite(value):
                    raise ValueError()
                status = 'breach' if value < target else 'ok'
                message = f'Annualized yield {value:.6f}; target {target:.6f}'
        except (KeyError, TypeError, ValueError, OverflowError):
            value = None
        result.append(dict(portfolio_code=key, portfolio_name=str(row.get('jjztmc') or key),
                           indicator_value=value, evaluation_status=status,
                           alert_level=2 if status in {'missing_data', 'invalid_data'} else int(status == 'breach'),
                           alert_message=f'[{status}] {message}'))
    return result
