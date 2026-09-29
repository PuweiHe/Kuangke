"""Resolve the identity expected by optional external data adapters."""

import os


def get_data_api_user_id() -> str:
    user_id = os.environ.get('DATA_API_USER_ID', '').strip()
    if not user_id:
        raise RuntimeError('DATA_API_USER_ID is required for this external data adapter')
    return user_id
