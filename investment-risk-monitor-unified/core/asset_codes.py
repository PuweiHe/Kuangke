"""Normalize supported security suffixes without dropping leading zeroes."""

def normalize_asset_code(value):
    if not isinstance(value, str) or not value.strip() or value.strip() == '.':
        raise ValueError('Asset code must be nonempty text')
    value = value.strip().upper()
    for suffix, replacement in (('.STK.SHSC', '.HK'), ('.STK.SZSC', '.HK'), ('.BOND.YHJ', '.IB')):
        if value.endswith(suffix):
            return value[:-len(suffix)] + replacement
    parts = value.split('.')
    if any(not p for p in parts):
        raise ValueError('Invalid asset code')
    return parts[0] + '.' + parts[-1] if len(parts) > 2 else value


def whitelist_violations(positions, whitelist):
    """An empty reference set is unavailable, not evidence of universal failure."""
    if not whitelist:
        raise ValueError('Whitelist reference data is unavailable')
    allowed = {normalize_asset_code(row['asset_code']) for row in whitelist}
    return [row for row in positions if normalize_asset_code(row['zcdm']) not in allowed]
