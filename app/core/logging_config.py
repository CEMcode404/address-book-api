"""Logging configuration for the application."""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger to write formatted logs to stdout.

    Args:
        level: Minimum log level to output (e.g. "DEBUG", "INFO").
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  #  Override any existing root handlers so our config always applies
    )
