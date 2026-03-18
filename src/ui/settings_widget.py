# -*- coding: utf-8 -*-
"""
Settings widget — store info form + pricing catalog view.
"""
import logging
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QTextEdit, QGroupBox, QTreeWidget,
    QTreeWidgetItem, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Ρυθμίσεις")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_store_tab(), "Στοιχεία Καταστήματος")
        tabs.addTab(self._build_pricing_tab(), "Τιμοκατάλογος")
        layout.addWidget(tabs)

    def _build_store_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        store = self._config.store_section

        self._store_name = QLineEdit(store.get('name', ''))
        form.addRow("Όνομα Καταστήματος:", self._store_name)

        self._store_address = QLineEdit(store.get('address', ''))
        form.addRow("Διεύθυνση:", self._store_address)

        self._store_phone = QLineEdit(store.get('phone', ''))
        form.addRow("Τηλέφωνο:", self._store_phone)

        self._store_tax = QLineEdit(store.get('tax_number', ''))
        form.addRow("ΑΦΜ:", self._store_tax)

        self._store_footer = QTextEdit(store.get('receipt_footer', ''))
        self._store_footer.setFixedHeight(60)
        form.addRow("Κείμενο Απόδειξης:", self._store_footer)

        layout.addLayout(form)
        layout.addSpacing(8)

        save_btn = QPushButton("Αποθήκευση")
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        save_btn.clicked.connect(self._on_save_store)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return widget

    def _build_pricing_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        note = QLabel(
            "Ο τιμοκατάλογος διαχειρίζεται μέσω του αρχείου config.json.\n"
            "Επεξεργαστείτε το αρχείο και επανεκκινήστε την εφαρμογή για αλλαγές."
        )
        note.setStyleSheet("color: #7f8c8d;")
        note.setWordWrap(True)
        layout.addWidget(note)

        open_btn = QPushButton("Άνοιγμα config.json")
        open_btn.clicked.connect(self._on_open_config)
        layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        tree = QTreeWidget()
        tree.setHeaderLabels(["Κατηγορία / Υπηρεσία", "Τιμή"])
        tree.setColumnWidth(0, 350)
        sym = self._config.currency_symbol

        for cat in self._config.pricing_categories:
            cat_item = QTreeWidgetItem(tree, [cat['label'], ""])
            cat_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            for svc_key, svc_data in cat.get('services', {}).items():
                svc_item = QTreeWidgetItem(cat_item, [
                    f"  {svc_data['label']}",
                    f"{sym}{svc_data['price']:.2f}"
                ])
            cat_item.setExpanded(True)

        layout.addWidget(tree)
        return widget

    def _on_save_store(self) -> None:
        data = {
            'name':           self._store_name.text().strip(),
            'address':        self._store_address.text().strip(),
            'phone':          self._store_phone.text().strip(),
            'tax_number':     self._store_tax.text().strip(),
            'receipt_footer': self._store_footer.toPlainText().strip(),
        }
        try:
            self._config.write_store_settings(data)
            QMessageBox.information(self, "Επιτυχία",
                                    "Οι ρυθμίσεις αποθηκεύτηκαν επιτυχώς.")
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης ρυθμίσεων: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _on_open_config(self) -> None:
        import sys
        from src.config import Config
        # Get config path
        if hasattr(self._config, '_path'):
            config_path = self._config._path
        else:
            config_path = "config.json"

        try:
            if sys.platform == 'win32':
                os.startfile(config_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{config_path}"')
            else:
                os.system(f'xdg-open "{config_path}"')
        except Exception as e:
            QMessageBox.information(self, "Πληροφορία",
                                    f"Αρχείο: {config_path}")
