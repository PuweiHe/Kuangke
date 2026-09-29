"""Payload tracing is disabled in the portfolio."""

def apply_request_logging():
    return None

def log_request(func):
    return func
