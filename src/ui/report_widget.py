# -*- coding: utf-8 -*-
"""
Revenue report widget — date range, grouping, CSV export.
"""
import logging
import os
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class ReportWidget(QWidget):
    def __init__(self, report_svc, config, parent=None):
        super().__init__(parent)
        self._report_svc = report_svc
        self._config = config
        self._rows = []
        self._total = 0.0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Εκθέσεις Εσόδων")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Date range + grouping row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Από:"))
        today = QDate.currentDate()
        first_of_month = QDate(today.year(), today.month(), 1)

        self._start_date = QDateEdit(first_of_month)
        self._start_date.setCalendarPopup(True)
        self._start_date.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self._start_date)

        filter_layout.addWidget(QLabel("Έως:"))
        self._end_date = QDateEdit(today)
        self._end_date.setCalendarPopup(True)
        self._end_date.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self._end_date)

        filter_layout.addSpacing(16)
        filter_layout.addWidget(QLabel("Ομαδοποίηση:"))
        self._group_combo = QComboBox()
        self._group_combo.addItem("Ημερήσια", "day")
        self._group_combo.addItem("Εβδομαδιαία", "week")
        self._group_combo.addItem("Μηνιαία", "month")
        filter_layout.addWidget(self._group_combo)

        run_btn = QPushButton("Εκτέλεση")
        run_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 6px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        run_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(run_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(
            ["Περίοδος", "Αρ. Παραγγελιών", "Σύνολο"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table)

        # Total + export
        bottom_layout = QHBoxLayout()
        self._total_label = QLabel("Συνολικά Έσοδα: €0.00")
        self._total_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        bottom_layout.addWidget(self._total_label)
        bottom_layout.addStretch()

        export_btn = QPushButton("Εξαγωγή CSV")
        export_btn.clicked.connect(self._on_export_csv)
        bottom_layout.addWidget(export_btn)
        layout.addLayout(bottom_layout)

    def refresh(self) -> None:
        start = self._start_date.date().toString("yyyy-MM-dd")
        end   = self._end_date.date().toString("yyyy-MM-dd")
        group = self._group_combo.currentData()
        sym   = self._config.currency_symbol
        try:
            self._rows  = self._report_svc.get_revenue(start, end, group)
            self._total = self._report_svc.get_total(start, end)

            self._table.setRowCount(len(self._rows))
            for row, data in enumerate(self._rows):
                self._table.setItem(row, 0, QTableWidgetItem(data.get('period', '')))
                self._table.setItem(row, 1, QTableWidgetItem(
                    str(data.get('order_count', 0))))
                self._table.setItem(row, 2, QTableWidgetItem(
                    f"{sym}{data.get('total', 0):.2f}"))

            self._total_label.setText(
                f"Συνολικά Έσοδα: {sym}{self._total:.2f}")
        except Exception as e:
            logger.error("Σφάλμα δημιουργίας έκθεσης: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _on_export_csv(self) -> None:
        if not self._rows:
            QMessageBox.information(self, "Πληροφορία",
                                    "Δεν υπάρχουν δεδομένα για εξαγωγή.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Αποθήκευση CSV",
            f"εκθεση_{date.today().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            self._report_svc.export_csv(
                self._rows, path, self._total, self._config.currency_symbol)
            QMessageBox.information(self, "Επιτυχία",
                                    f"Το αρχείο αποθηκεύτηκε:\n{path}")
        except Exception as e:
            logger.error("Σφάλμα εξαγωγής CSV: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")
