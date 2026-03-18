# -*- coding: utf-8 -*-
"""
Customer management widget — list + CRUD dialogs.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QMessageBox, QDialog, QFormLayout, QLineEdit as QLE, QTextEdit,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.models.customer import Customer

logger = logging.getLogger(__name__)


class CustomerWidget(QWidget):
    def __init__(self, customer_svc, parent=None):
        super().__init__(parent)
        self._customer_svc = customer_svc
        self._customers = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Πελάτες")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Αναζήτηση:"))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Όνομα, τηλέφωνο ή email…")
        self._search_box.textChanged.connect(self._apply_search)
        self._search_box.setFixedWidth(280)
        search_layout.addWidget(self._search_box)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Όνομα", "Τηλέφωνο", "Email", "Παραγγελίες", "Εγγραφή"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)

        # Actions
        action_layout = QHBoxLayout()
        self._new_btn = QPushButton("➕  Νέος Πελάτης")
        self._new_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 6px 14px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        self._new_btn.clicked.connect(self._on_new)
        action_layout.addWidget(self._new_btn)

        self._edit_btn = QPushButton("✏️  Επεξεργασία")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit)
        action_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("🗑️  Διαγραφή")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet(
            "QPushButton { background: #e74c3c; color: white; border-radius: 4px; "
            "padding: 6px 14px; }"
            "QPushButton:disabled { background: #bdc3c7; }"
            "QPushButton:hover:!disabled { background: #c0392b; }"
        )
        self._delete_btn.clicked.connect(self._on_delete)
        action_layout.addWidget(self._delete_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

    def refresh(self) -> None:
        try:
            self._customers = self._customer_svc.list_customers()
            self._populate_table(self._customers)
        except Exception as e:
            logger.error("Σφάλμα φόρτωσης πελατών: %s", e, exc_info=True)

    def _apply_search(self) -> None:
        query = self._search_box.text().strip()
        try:
            results = self._customer_svc.search_customers(query)
            self._populate_table(results)
        except Exception as e:
            logger.error("Σφάλμα αναζήτησης: %s", e, exc_info=True)

    def _populate_table(self, customers: list) -> None:
        self._table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self._table.setItem(row, 0, QTableWidgetItem(c.name))
            self._table.setItem(row, 1, QTableWidgetItem(c.phone))
            self._table.setItem(row, 2, QTableWidgetItem(c.email))
            self._table.setItem(row, 3, QTableWidgetItem(str(c.order_count)))
            date_str = c.created_at[:10] if c.created_at else ""
            self._table.setItem(row, 4, QTableWidgetItem(date_str))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, c.id)
        self._on_selection_changed()

    def _get_selected_id(self) -> int | None:
        row = self._table.currentRow()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_selection_changed(self) -> None:
        has_sel = self._get_selected_id() is not None
        self._edit_btn.setEnabled(has_sel)
        self._delete_btn.setEnabled(has_sel)

    def _on_new(self) -> None:
        dlg = CustomerFormDialog(self._customer_svc, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self) -> None:
        cid = self._get_selected_id()
        if not cid:
            return
        customer = self._customer_svc.get_customer(cid)
        if customer:
            dlg = CustomerFormDialog(self._customer_svc, customer=customer, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh()

    def _on_delete(self) -> None:
        cid = self._get_selected_id()
        if not cid:
            return
        has_orders = self._customer_svc.has_orders(cid)
        if has_orders:
            reply = QMessageBox.question(
                self, "Επιβεβαίωση Διαγραφής",
                "Ο πελάτης έχει παραγγελίες. Είστε σίγουροι ότι θέλετε να τον διαγράψετε;",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, "Επιβεβαίωση Διαγραφής",
                "Είστε σίγουροι ότι θέλετε να διαγράψετε αυτόν τον πελάτη;",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        try:
            self._customer_svc.delete_customer(cid, force=True)
            self.refresh()
        except Exception as e:
            logger.error("Σφάλμα διαγραφής πελάτη: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα διαγραφής: {e}")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()


class CustomerFormDialog(QDialog):
    def __init__(self, customer_svc, customer: Customer = None, parent=None):
        super().__init__(parent)
        self._customer_svc = customer_svc
        self._customer = customer
        is_edit = customer is not None
        self.setWindowTitle("Επεξεργασία Πελάτη" if is_edit else "Νέος Πελάτης")
        self.setMinimumWidth(400)
        self._setup_ui(is_edit)

    def _setup_ui(self, is_edit: bool) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name = QLineEdit(self._customer.name if is_edit else "")
        self._name.setPlaceholderText("Υποχρεωτικό")
        form.addRow("Όνομα *:", self._name)

        self._phone = QLineEdit(self._customer.phone if is_edit else "")
        form.addRow("Τηλέφωνο:", self._phone)

        self._email = QLineEdit(self._customer.email if is_edit else "")
        form.addRow("Email:", self._email)

        self._address = QLineEdit(self._customer.address if is_edit else "")
        form.addRow("Διεύθυνση:", self._address)

        self._notes = QTextEdit(self._customer.notes if is_edit else "")
        self._notes.setFixedHeight(80)
        form.addRow("Σημειώσεις:", self._notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Αποθήκευση")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Προσοχή", "Το όνομα είναι υποχρεωτικό.")
            return
        try:
            if self._customer:
                self._customer.name    = name
                self._customer.phone   = self._phone.text().strip()
                self._customer.email   = self._email.text().strip()
                self._customer.address = self._address.text().strip()
                self._customer.notes   = self._notes.toPlainText().strip()
                self._customer_svc.update_customer(self._customer)
            else:
                self._customer_svc.create_customer(
                    name=name,
                    phone=self._phone.text().strip(),
                    email=self._email.text().strip(),
                    address=self._address.text().strip(),
                    notes=self._notes.toPlainText().strip(),
                )
            self.accept()
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης πελάτη: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")
