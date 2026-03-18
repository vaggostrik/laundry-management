# -*- coding: utf-8 -*-
"""
Receipt preview dialog + print button.
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.printing.receipt_printer import ReceiptPrinter

logger = logging.getLogger(__name__)


class ReceiptDialog(QDialog):
    def __init__(self, order, config, parent=None):
        super().__init__(parent)
        self._order = order
        self._config = config
        self._printer = ReceiptPrinter(config)
        self.setWindowTitle(f"Απόδειξη — Παραγγελία #{order.id}")
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        label = QLabel(f"Απόδειξη Παραγγελίας #{self._order.id}")
        label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(label)

        # Plain-text preview
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("Courier New", 10))
        self._preview.setMinimumHeight(320)

        lines = self._printer.build_receipt_lines(self._order)
        self._preview.setPlainText("\n".join(lines))
        layout.addWidget(self._preview)

        # Buttons
        btn_layout = QHBoxLayout()

        print_btn = QPushButton("🖨️  Εκτύπωση")
        print_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        print_btn.clicked.connect(self._on_print)
        btn_layout.addWidget(print_btn)

        pdf_btn = QPushButton("📄  Αποθήκευση PDF")
        pdf_btn.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #229954; }"
        )
        pdf_btn.clicked.connect(self._on_save_pdf)
        btn_layout.addWidget(pdf_btn)

        close_btn = QPushButton("Κλείσιμο")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_print(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        try:
            self._printer.print_receipt(self._order, parent=self)
        except Exception as e:
            logger.error("Σφάλμα εκτύπωσης: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα Εκτύπωσης",
                                 f"Δεν ήταν δυνατή η εκτύπωση.\n\n{e}")

    def _on_save_pdf(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        try:
            saved = self._printer.save_as_pdf(self._order, parent=self)
            if saved:
                QMessageBox.information(self, "Επιτυχία",
                                        "Η απόδειξη αποθηκεύτηκε ως PDF.")
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης PDF: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα",
                                 f"Δεν ήταν δυνατή η αποθήκευση PDF.\n\n{e}")
