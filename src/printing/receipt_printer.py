# -*- coding: utf-8 -*-
"""
Receipt printing via QPrinter + QPainter.
Supports: physical printer (via QPrintDialog) and PDF export.
"""
import logging
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont, QPageSize
from PyQt6.QtWidgets import QDialog, QFileDialog

logger = logging.getLogger(__name__)


class ReceiptPrinter:
    def __init__(self, config):
        self._config = config

    def build_receipt_lines(self, order) -> list[str]:
        sym = self._config.currency_symbol
        lines = []
        lines.append(self._config.store_name)
        if self._config.store_address:
            lines.append(self._config.store_address)
        if self._config.store_phone:
            lines.append(f"Τηλ: {self._config.store_phone}")
        if self._config.store_tax_number:
            lines.append(f"ΑΦΜ: {self._config.store_tax_number}")
        lines.append("─" * 42)
        lines.append(f"Παραγγελία #: {order.id}")
        lines.append(
            f"Ημερομηνία:   "
            f"{order.received_at[:16] if order.received_at else '—'}"
        )
        lines.append(f"Πελάτης:      {order.customer_name}")
        lines.append("─" * 42)

        for item in order.items:
            lines.append(item.item_name)
            lines.append(
                f"  {item.quantity} x {sym}{item.unit_price:.2f}"
                f" = {sym}{item.subtotal:.2f}"
            )

        lines.append("─" * 42)
        lines.append(f"ΣΥΝΟΛΟ:  {sym}{order.total_amount:.2f}")
        lines.append("─" * 42)
        if order.notes:
            lines.append(f"Σημ: {order.notes}")
        lines.append("")
        if self._config.receipt_footer:
            lines.append(self._config.receipt_footer)
        return lines

    def _paint_lines(self, printer: QPrinter, lines: list[str]) -> None:
        painter = QPainter(printer)
        painter.setFont(QFont("Courier New", 10))
        fm = painter.fontMetrics()
        line_h = fm.height() + 4
        x, y = 100, 100
        for line in lines:
            painter.drawText(x, y, line)
            y += line_h
            # New page if we're past the bottom margin
            if y > printer.pageLayout().paintRectPixels(printer.resolution()).height() - 100:
                printer.newPage()
                y = 100
        painter.end()

    def print_receipt(self, order, parent=None) -> bool:
        """Open the system print dialog and print to the selected printer."""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        dlg = QPrintDialog(printer, parent)
        dlg.setWindowTitle("Εκτύπωση Απόδειξης")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False

        lines = self.build_receipt_lines(order)
        self._paint_lines(printer, lines)
        logger.info("Εκτυπώθηκε απόδειξη παραγγελίας #%d", order.id)
        return True

    def save_as_pdf(self, order, parent=None) -> bool:
        """Export the receipt to a PDF file chosen by the user."""
        path, _ = QFileDialog.getSaveFileName(
            parent,
            "Αποθήκευση Απόδειξης ως PDF",
            f"αποδειξη_{order.id}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return False

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)

        lines = self.build_receipt_lines(order)
        self._paint_lines(printer, lines)
        logger.info("Αποδειξη #%d αποθηκεύτηκε ως PDF: %s", order.id, path)
        return True
