"""Logging configuration."""

import logging

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(debug: bool = False) -> None:
    """Configure root logging for the application.

    Args:
        debug: Whether to log at DEBUG level instead of INFO.
    """
    logging.basicConfig(
        format=LOG_FORMAT,
        level=logging.DEBUG if debug else logging.INFO,
    )
    # httpx logs every request URL at INFO, which includes the bot token.
    logging.getLogger("httpx").setLevel(logging.WARNING)
