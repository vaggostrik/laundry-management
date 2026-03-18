# -*- coding: utf-8 -*-
"""
New order dialog — dynamic items, cascading comboboxes, live total.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QCompleter, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtGui import QFont

from src.ui.receipt_dialog import ReceiptDialog

logger = logging.getLogger(__name__)


class NewOrderDialog(QDialog):
    order_created = pyqtSignal(int)

    def __init__(self, order_svc, customer_svc, config, parent=None):
        super().__init__(parent)
        self._order_svc = order_svc
        self._customer_svc = customer_svc
        self._config = config
        self._customers = []

        self.setWindowTitle("Νέα Παραγγελία")
        self.setMinimumWidth(720)
        self.setMinimumHeight(520)
        self._setup_ui()
        self._load_customers()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Νέα Παραγγελία")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # ── Customer row ──────────────────────────────────────────────────────
        cust_layout = QHBoxLayout()
        cust_layout.addWidget(QLabel("Πελάτης:"))

        self._customer_combo = QComboBox()
        self._customer_combo.setEditable(True)
        self._customer_combo.setMinimumWidth(300)
        self._customer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cust_layout.addWidget(self._customer_combo)

        new_cust_btn = QPushButton("+ Νέος Πελάτης")
        new_cust_btn.clicked.connect(self._on_new_customer)
        cust_layout.addWidget(new_cust_btn)
        cust_layout.addStretch()
        layout.addLayout(cust_layout)

        # ── Items table ───────────────────────────────────────────────────────
        layout.addWidget(QLabel("Είδη:"))

        self._items_table = QTableWidget(0, 5)
        self._items_table.setHorizontalHeaderLabels(
            ["Κατηγορία", "Υπηρεσία", "Τεμ.", "Τιμή/τεμ.", "Υποσύνολο"]
        )
        self._items_table.verticalHeader().setVisible(False)
        hh = self._items_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._items_table.setFixedHeight(200)
        layout.addWidget(self._items_table)

        add_item_btn = QPushButton("+ Προσθήκη Είδους")
        add_item_btn.clicked.connect(self._add_item_row)
        layout.addWidget(add_item_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # ── Notes ─────────────────────────────────────────────────────────────
        layout.addWidget(QLabel("Σημειώσεις:"))
        self._notes = QTextEdit()
        self._notes.setFixedHeight(60)
        self._notes.setPlaceholderText("Προαιρετικές σημειώσεις…")
        layout.addWidget(self._notes)

        # ── Total ─────────────────────────────────────────────────────────────
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self._total_label = QLabel("Σύνολο: €0.00")
        self._total_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        total_layout.addWidget(self._total_label)
        layout.addLayout(total_layout)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Ακύρωση")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._save_btn = QPushButton("Αποθήκευση & Εκτύπωση")
        self._save_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        layout.addLayout(btn_layout)

        # Add one initial row
        self._add_item_row()

    def _load_customers(self) -> None:
        try:
            self._customers = self._customer_svc.list_customers()
            self._customer_combo.clear()
            names = [c.name for c in self._customers]
            self._customer_combo.addItems(names)
            completer = QCompleter(names, self)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self._customer_combo.setCompleter(completer)
        except Exception as e:
            logger.error("Σφάλμα φόρτωσης πελατών: %s", e, exc_info=True)

    def _add_item_row(self) -> None:
        row = self._items_table.rowCount()
        self._items_table.insertRow(row)

        # Category combobox
        cat_combo = QComboBox()
        categories = self._config.pricing_categories
        for cat in categories:
            cat_combo.addItem(cat['label'], cat['key'])

        # Service combobox
        svc_combo = QComboBox()

        def update_services(idx, cc=cat_combo, sc=svc_combo):
            cat_key = cc.currentData()
            services = self._config.get_category_services(cat_key)
            sc.clear()
            for svc_key, svc_data in services.items():
                sc.addItem(svc_data['label'], svc_key)
            self._update_row_price(self._items_table.indexAt(cc.pos()).row()
                                   if hasattr(cc, 'pos') else
                                   self._find_row(cc))

        cat_combo.currentIndexChanged.connect(lambda idx, r=row: self._on_category_changed(r))
        svc_combo.currentIndexChanged.connect(lambda idx, r=row: self._on_service_changed(r))

        # Quantity spinbox
        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setMaximum(999)
        qty_spin.setValue(1)
        qty_spin.valueChanged.connect(lambda val, r=row: self._update_row_price(r))

        # Price and subtotal labels
        price_item   = QTableWidgetItem("€0.00")
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        subtotal_item = QTableWidgetItem("€0.00")
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self._items_table.setCellWidget(row, 0, cat_combo)
        self._items_table.setCellWidget(row, 1, svc_combo)
        self._items_table.setCellWidget(row, 2, qty_spin)
        self._items_table.setItem(row, 3, price_item)
        self._items_table.setItem(row, 4, subtotal_item)

        # Initialize services for first category
        self._populate_services(row)
        self._update_row_price(row)

    def _populate_services(self, row: int) -> None:
        cat_combo = self._items_table.cellWidget(row, 0)
        svc_combo = self._items_table.cellWidget(row, 1)
        if not cat_combo or not svc_combo:
            return
        cat_key = cat_combo.currentData()
        services = self._config.get_category_services(cat_key)
        svc_combo.blockSignals(True)
        svc_combo.clear()
        for svc_key, svc_data in services.items():
            svc_combo.addItem(svc_data['label'], svc_key)
        svc_combo.blockSignals(False)

    def _on_category_changed(self, row: int) -> None:
        self._populate_services(row)
        self._update_row_price(row)

    def _on_service_changed(self, row: int) -> None:
        self._update_row_price(row)

    def _update_row_price(self, row: int) -> None:
        cat_combo = self._items_table.cellWidget(row, 0)
        svc_combo = self._items_table.cellWidget(row, 1)
        qty_spin  = self._items_table.cellWidget(row, 2)
        if not cat_combo or not svc_combo or not qty_spin:
            return
        cat_key = cat_combo.currentData()
        svc_key = svc_combo.currentData()
        if not cat_key or not svc_key:
            return
        price = self._config.get_item_price(cat_key, svc_key)
        qty = qty_spin.value()
        subtotal = price * qty
        sym = self._config.currency_symbol

        price_item = self._items_table.item(row, 3)
        if price_item:
            price_item.setText(f"{sym}{price:.2f}")
        subtotal_item = self._items_table.item(row, 4)
        if subtotal_item:
            subtotal_item.setText(f"{sym}{subtotal:.2f}")

        self._update_total()

    def _update_total(self) -> None:
        total = 0.0
        sym = self._config.currency_symbol
        for row in range(self._items_table.rowCount()):
            item = self._items_table.item(row, 4)
            if item:
                try:
                    total += float(item.text().replace(sym, '').replace(',', '.'))
                except ValueError:
                    pass
        self._total_label.setText(f"Σύνολο: {sym}{total:.2f}")

    def _find_row(self, widget) -> int:
        for row in range(self._items_table.rowCount()):
            if self._items_table.cellWidget(row, 0) is widget:
                return row
        return 0

    def _on_new_customer(self) -> None:
        from src.ui.customer_widget import CustomerFormDialog
        dlg = CustomerFormDialog(self._customer_svc, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_customers()
            # Select the newly added customer (last one)
            if self._customers:
                self._customer_combo.setCurrentIndex(len(self._customers) - 1)

    def _get_selected_customer_id(self) -> int | None:
        name = self._customer_combo.currentText().strip()
        for c in self._customers:
            if c.name == name:
                return c.id
        return None

    def _collect_items_data(self) -> list[dict]:
        items = []
        for row in range(self._items_table.rowCount()):
            cat_combo = self._items_table.cellWidget(row, 0)
            svc_combo = self._items_table.cellWidget(row, 1)
            qty_spin  = self._items_table.cellWidget(row, 2)
            if cat_combo and svc_combo and qty_spin:
                items.append({
                    'category_key': cat_combo.currentData(),
                    'service_key':  svc_combo.currentData(),
                    'quantity':     qty_spin.value(),
                })
        return items

    def _on_save(self) -> None:
        customer_id = self._get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "Προσοχή",
                                "Παρακαλώ επιλέξτε ή δημιουργήστε πελάτη.")
            return

        items_data = self._collect_items_data()
        if not items_data:
            QMessageBox.warning(self, "Προσοχή",
                                "Παρακαλώ προσθέστε τουλάχιστον ένα είδος.")
            return

        notes = self._notes.toPlainText().strip()
        try:
            order = self._order_svc.create_order(customer_id, items_data, notes)
            self.order_created.emit(order.id)
            dlg = ReceiptDialog(order, self._config, self)
            dlg.exec()
            self.accept()
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης παραγγελίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα",
                                 f"Δεν ήταν δυνατή η αποθήκευση της παραγγελίας.\n{e}")
