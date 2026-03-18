# -*- coding: utf-8 -*-
"""
Revenue reporting and CSV export.
"""
import csv
import logging
import os
from src.database.report_repo import ReportRepository

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, report_repo: ReportRepository, config):
        self._repo = report_repo
        self._config = config

    def get_revenue(self, start: str, end: str,
                    group_by: str = "day") -> list[dict]:
        """group_by: 'day', 'week', 'month'"""
        if group_by == "week":
            return self._repo.revenue_by_week(start, end)
        elif group_by == "month":
            return self._repo.revenue_by_month(start, end)
        return self._repo.revenue_by_day(start, end)

    def get_total(self, start: str, end: str) -> float:
        return self._repo.total_in_range(start, end)

    def export_csv(self, rows: list[dict], file_path: str,
                   total: float, currency: str = "€") -> None:
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Περίοδος", "Αρ. Παραγγελιών", f"Σύνολο ({currency})"])
                for row in rows:
                    writer.writerow([
                        row.get('period', ''),
                        row.get('order_count', 0),
                        round(row.get('total', 0), 2),
                    ])
                writer.writerow([])
                writer.writerow(["Γενικό Σύνολο", "", round(total, 2)])
            logger.info("Εξαγωγή CSV: %s", file_path)
        except Exception as e:
            logger.error("Σφάλμα εξαγωγής CSV: %s", e, exc_info=True)
            raise
