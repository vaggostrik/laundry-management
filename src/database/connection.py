# -*- coding: utf-8 -*-
"""
SQLite connection manager — singleton pattern.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._connect()

    def _connect(self) -> None:
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.commit()
        logger.debug("SQLite σύνδεση ανοίχτηκε: %s", self._db_path)

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._connect()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("SQLite σύνδεση έκλεισε")
