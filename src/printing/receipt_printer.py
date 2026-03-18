# -*- coding: utf-8 -*-
"""
Receipt printing via QPrinter + QPainter.
"""
import logging
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class ReceiptPrinter:
    def __init__(self, config):
        self._config = config

    def build_receipt_lines(self, order) -> list[str]:
        sym = self._config.currency_symbol
        lines = []
        lines.append(self._config.store_name)
        lines.append(self._config.store_address)
        lines.append(f"Τηλ: {self._config.store_phone}")
        if self._config.store_tax_number:
            lines.append(f"ΑΦΜ: {self._config.store_tax_number}")
        lines.append("─" * 40)
        lines.append(f"Παραγγελία #: {order.id}")
        lines.append(f"Ημερομηνία: {order.received_at[:16] if order.received_at else '—'}")
        lines.append(f"Πελάτης: {order.customer_name}")
        lines.append("─" * 40)

        for item in order.items:
            name_part = item.item_name[:25] if len(item.item_name) > 25 else item.item_name
            lines.append(
                f"{name_part}"
            )
            lines.append(
                f"  {item.quantity} x {sym}{item.unit_price:.2f} = {sym}{item.subtotal:.2f}"
            )

        lines.append("─" * 40)
        lines.append(f"ΣΥΝΟΛΟ: {sym}{order.total_amount:.2f}")
        lines.append("─" * 40)
        if order.notes:
            lines.append(f"Σημ: {order.notes}")
        lines.append("")
        lines.append(self._config.receipt_footer)
        return lines

    def print_receipt(self, order, parent=None) -> bool:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPrinter.PageSize.A4)

        dlg = QPrintDialog(printer, parent)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return False

        painter = QPainter(printer)
        font = QFont("Courier New", 10)
        painter.setFont(font)

        lines = self.build_receipt_lines(order)
        fm = painter.fontMetrics()
        line_height = fm.height() + 4
        x = 100
        y = 100

        for line in lines:
            painter.drawText(x, y, line)
            y += line_height

        painter.end()
        logger.info("Εκτυπώθηκε απόδειξη παραγγελίας #%d", order.id)
        return True
