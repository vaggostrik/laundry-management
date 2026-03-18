# -*- coding: utf-8 -*-
"""
Dashboard widget — summary cards + recent orders table.
"""
import logging
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.ui.widgets.summary_card import SummaryCard
from src.models.enums import OrderStatus

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    new_order_requested = pyqtSignal()

    def __init__(self, order_svc, config, parent=None):
        super().__init__(parent)
        self._order_svc = order_svc
        self._config = config
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Πίνακας Ελέγχου")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._date_label = QLabel()
        self._date_label.setStyleSheet("color: #7f8c8d; font-size: 11pt;")
        header_layout.addWidget(self._date_label)
        layout.addLayout(header_layout)

        # Summary cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._card_pending = SummaryCard("Σε Αναμονή", "0", "#e67e22")
        self._card_ready   = SummaryCard("Έτοιμα",     "0", "#3498db")
        self._card_revenue = SummaryCard("Έσοδα Σήμερα", "€0.00", "#27ae60")

        for card in [self._card_pending, self._card_ready, self._card_revenue]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setFixedHeight(100)
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        # Recent orders section
        section_label = QLabel("Πρόσφατες Παραγγελίες")
        section_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(section_label)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["#", "Πελάτης", "Υπηρεσίες", "Ποσό", "Κατάσταση"]
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table)

        # New order button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        new_order_btn = QPushButton("➕  Νέα Παραγγελία")
        new_order_btn.setFixedHeight(40)
        new_order_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 20px; font-weight: bold; font-size: 11pt; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        new_order_btn.clicked.connect(self.new_order_requested)
        btn_layout.addWidget(new_order_btn)
        layout.addLayout(btn_layout)

    def refresh(self) -> None:
        try:
            today = date.today().strftime(self._config.date_format)
            self._date_label.setText(f"Σήμερα: {today}")

            pending = self._order_svc.count_pending()
            ready   = self._order_svc.count_ready()
            revenue = self._order_svc.revenue_today()
            sym     = self._config.currency_symbol

            self._card_pending.set_value(str(pending))
            self._card_ready.set_value(str(ready))
            self._card_revenue.set_value(f"{sym}{revenue:.2f}")

            orders = self._order_svc.get_recent_orders(10)
            self._table.setRowCount(len(orders))
            for row, order in enumerate(orders):
                self._table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self._table.setItem(row, 1, QTableWidgetItem(order.customer_name))
                items_summary = f"{len(order.items)} είδ." if order.items else "—"
                self._table.setItem(row, 2, QTableWidgetItem(items_summary))
                self._table.setItem(row, 3, QTableWidgetItem(
                    f"{sym}{order.total_amount:.2f}"))
                self._table.setItem(row, 4, QTableWidgetItem(
                    order.status.greek_label))
        except Exception as e:
            logger.error("Σφάλμα ανανέωσης dashboard: %s", e, exc_info=True)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()
