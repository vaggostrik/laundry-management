# -*- coding: utf-8 -*-
"""
Colored status label widget.
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from src.models.enums import OrderStatus


class StatusBadge(QLabel):
    _COLORS = {
        OrderStatus.RECEIVED:  ("#f39c12", "white"),
        OrderStatus.READY:     ("#3498db", "white"),
        OrderStatus.DELIVERED: ("#27ae60", "white"),
    }

    def __init__(self, status: OrderStatus, parent=None):
        super().__init__(parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_status(self, status: OrderStatus) -> None:
        bg, fg = self._COLORS.get(status, ("#95a5a6", "white"))
        self.setText(status.greek_label)
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border-radius: 4px; "
            f"padding: 2px 8px; font-weight: bold;"
        )
