# -*- coding: utf-8 -*-
"""
Dashboard summary card widget.
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SummaryCard(QFrame):
    def __init__(self, label: str, value: str = "0",
                 color: str = "#2c3e50", parent=None):
        super().__init__(parent)
        self.setObjectName("summary_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame#summary_card { background: white; border-radius: 8px; "
            "border: 1px solid #ddd; padding: 12px; }"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("card_value")
        font = QFont()
        font.setPointSize(22)
        font.setBold(True)
        self._value_label.setFont(font)
        self._value_label.setStyleSheet(f"color: {color};")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._text_label = QLabel(label)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setStyleSheet("color: #7f8c8d; font-size: 10pt;")

        layout.addWidget(self._value_label)
        layout.addWidget(self._text_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)
