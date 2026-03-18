# -*- coding: utf-8 -*-
"""
Order management widget — list, filter, status workflow.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QMessageBox, QDialog, QFormLayout, QTextEdit,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.models.enums import OrderStatus

logger = logging.getLogger(__name__)


class OrderManagementWidget(QWidget):
    new_order_requested = pyqtSignal()

    def __init__(self, order_svc, config, parent=None):
        super().__init__(parent)
        self._order_svc = order_svc
        self._config = config
        self._orders = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Παραγγελίες")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("➕  Νέα Παραγγελία")
        new_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 6px 14px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        new_btn.clicked.connect(self.new_order_requested)
        header.addWidget(new_btn)
        layout.addLayout(header)

        # Filter + search row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Φίλτρο:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("Όλες", None)
        for s in OrderStatus:
            self._status_filter.addItem(s.greek_label, s)
        self._status_filter.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._status_filter)

        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Αναζήτηση:"))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Όνομα ή αρ. παραγγελίας…")
        self._search_box.textChanged.connect(self._apply_filter)
        self._search_box.setFixedWidth(220)
        filter_layout.addWidget(self._search_box)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Ημ/νία", "Πελάτης", "Ποσό", "Κατάσταση", ""]
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Bottom action buttons
        action_layout = QHBoxLayout()
        self._advance_btn = QPushButton("Επόμενη Κατάσταση")
        self._advance_btn.setEnabled(False)
        self._advance_btn.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:disabled { background: #bdc3c7; }"
            "QPushButton:hover:!disabled { background: #229954; }"
        )
        self._advance_btn.clicked.connect(self._on_advance_status)
        action_layout.addWidget(self._advance_btn)

        self._detail_btn = QPushButton("Λεπτομέρειες")
        self._detail_btn.setEnabled(False)
        self._detail_btn.clicked.connect(self._on_show_detail)
        action_layout.addWidget(self._detail_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

    def refresh(self) -> None:
        try:
            self._orders = self._order_svc.get_all_orders()
            self._apply_filter()
        except Exception as e:
            logger.error("Σφάλμα φόρτωσης παραγγελιών: %s", e, exc_info=True)

    def _apply_filter(self) -> None:
        status_filter = self._status_filter.currentData()
        search_text = self._search_box.text().strip().lower()

        filtered = self._orders
        if status_filter is not None:
            filtered = [o for o in filtered if o.status == status_filter]
        if search_text:
            filtered = [o for o in filtered if
                        search_text in o.customer_name.lower() or
                        search_text in str(o.id)]

        self._table.setRowCount(len(filtered))
        sym = self._config.currency_symbol
        fmt = self._config.date_format

        for row, order in enumerate(filtered):
            self._table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            date_str = order.received_at[:10] if order.received_at else ""
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                date_str = dt.strftime(fmt)
            except Exception:
                pass
            self._table.setItem(row, 1, QTableWidgetItem(date_str))
            self._table.setItem(row, 2, QTableWidgetItem(order.customer_name))
            self._table.setItem(row, 3, QTableWidgetItem(
                f"{sym}{order.total_amount:.2f}"))
            self._table.setItem(row, 4, QTableWidgetItem(order.status.greek_label))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, order.id)

        self._on_selection_changed()

    def _get_selected_order_id(self) -> int | None:
        rows = self._table.selectedItems()
        if not rows:
            return None
        row = self._table.currentRow()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _get_selected_order(self):
        order_id = self._get_selected_order_id()
        if order_id is None:
            return None
        for o in self._orders:
            if o.id == order_id:
                return o
        return None

    def _on_selection_changed(self) -> None:
        order = self._get_selected_order()
        has_sel = order is not None
        self._detail_btn.setEnabled(has_sel)

        can_advance = has_sel and order.status != OrderStatus.DELIVERED
        self._advance_btn.setEnabled(can_advance)
        if can_advance:
            next_s = order.status.next_status()
            self._advance_btn.setText(
                f"Σημείωση ως '{next_s.greek_label}'" if next_s else "—"
            )
        else:
            self._advance_btn.setText("Επόμενη Κατάσταση")

    def _on_advance_status(self) -> None:
        order_id = self._get_selected_order_id()
        if not order_id:
            return
        try:
            new_status = self._order_svc.advance_status(order_id)
            self.refresh()
            QMessageBox.information(
                self, "Επιτυχία",
                f"Η κατάσταση άλλαξε σε: {new_status.greek_label}"
            )
        except Exception as e:
            logger.error("Σφάλμα αλλαγής κατάστασης: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα",
                                 f"Δεν ήταν δυνατή η αλλαγή κατάστασης.\n{e}")

    def _on_double_click(self) -> None:
        self._on_show_detail()

    def _on_show_detail(self) -> None:
        order_id = self._get_selected_order_id()
        if not order_id:
            return
        try:
            order = self._order_svc.get_order(order_id)
            if order:
                dlg = OrderDetailDialog(order, self._config, self)
                dlg.exec()
        except Exception as e:
            logger.error("Σφάλμα φόρτωσης λεπτομερειών: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()


class OrderDetailDialog(QDialog):
    def __init__(self, order, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Παραγγελία #{order.id}")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        sym = config.currency_symbol
        fmt = config.date_format

        info = QFormLayout()
        info.addRow("Πελάτης:", QLabel(order.customer_name))
        info.addRow("Κατάσταση:", QLabel(order.status.greek_label))
        info.addRow("Παραλήφθηκε:", QLabel(
            order.received_at[:16] if order.received_at else "—"))
        info.addRow("Σύνολο:", QLabel(f"{sym}{order.total_amount:.2f}"))
        layout.addLayout(info)

        layout.addWidget(QLabel("Είδη:"))
        items_table = QTableWidget(len(order.items), 4)
        items_table.setHorizontalHeaderLabels(
            ["Είδος", "Τεμ.", "Τιμή/τεμ.", "Υποσύνολο"])
        items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        items_table.verticalHeader().setVisible(False)
        items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        for row, item in enumerate(order.items):
            items_table.setItem(row, 0, QTableWidgetItem(item.item_name))
            items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            items_table.setItem(row, 2, QTableWidgetItem(
                f"{sym}{item.unit_price:.2f}"))
            items_table.setItem(row, 3, QTableWidgetItem(
                f"{sym}{item.subtotal:.2f}"))
        layout.addWidget(items_table)

        if order.notes:
            layout.addWidget(QLabel(f"Σημειώσεις: {order.notes}"))

        close_btn = QPushButton("Κλείσιμο")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
