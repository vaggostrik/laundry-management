# -*- coding: utf-8 -*-
"""
Report repository — revenue queries.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


class ReportRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def revenue_by_day(self, start: str, end: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT date(received_at) as period,
                      COUNT(*) as order_count,
                      COALESCE(SUM(total_amount), 0) as total
               FROM orders
               WHERE date(received_at) BETWEEN date(?) AND date(?)
               GROUP BY period
               ORDER BY period""",
            (start, end)
        ).fetchall()
        return [dict(r) for r in rows]

    def revenue_by_week(self, start: str, end: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT strftime('%Y-W%W', received_at) as period,
                      COUNT(*) as order_count,
                      COALESCE(SUM(total_amount), 0) as total
               FROM orders
               WHERE date(received_at) BETWEEN date(?) AND date(?)
               GROUP BY period
               ORDER BY period""",
            (start, end)
        ).fetchall()
        return [dict(r) for r in rows]

    def revenue_by_month(self, start: str, end: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT strftime('%Y-%m', received_at) as period,
                      COUNT(*) as order_count,
                      COALESCE(SUM(total_amount), 0) as total
               FROM orders
               WHERE date(received_at) BETWEEN date(?) AND date(?)
               GROUP BY period
               ORDER BY period""",
            (start, end)
        ).fetchall()
        return [dict(r) for r in rows]

    def total_in_range(self, start: str, end: str) -> float:
        row = self._conn.execute(
            """SELECT COALESCE(SUM(total_amount), 0)
               FROM orders
               WHERE date(received_at) BETWEEN date(?) AND date(?)""",
            (start, end)
        ).fetchone()
        return row[0]
