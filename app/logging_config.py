import logging

import structlog


def order_log_keys(_, __, event_dict: dict) -> dict:
    """Ensure stable JSON key order: core metadata first, then custom fields."""
    preferred_order = ('timestamp', 'logger', 'level', 'request_id', 'event')
    ordered = {key: event_dict[key] for key in preferred_order if key in event_dict}

    for key, value in event_dict.items():
        if key not in ordered:
            ordered[key] = value

    return ordered


def configure_logging() -> None:
    """Configure stdlib logging and structlog once for the process."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if structlog.is_configured():
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            order_log_keys,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
