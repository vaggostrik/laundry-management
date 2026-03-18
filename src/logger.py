# -*- coding: utf-8 -*-
"""
Logging setup with rotating file handler supporting UTF-8 (Greek text).
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_path: str, log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating file handler — UTF-8 mandatory for Greek text
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    fh = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    fh.setFormatter(fmt)
    root_logger.addHandler(fh)

    # Console handler for development
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root_logger.addHandler(ch)
