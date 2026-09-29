"""Console logging only; payload logging is intentionally excluded."""
import logging
logger = logging.getLogger('portfolio')
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
