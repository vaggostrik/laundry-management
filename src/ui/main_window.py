# -*- coding: utf-8 -*-
"""
Main application window with sidebar navigation.
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from src.database.connection import DatabaseConnection
from src.database.customer_repo import CustomerRepository
from src.database.order_repo import OrderRepository
from src.database.report_repo import ReportRepository
from src.services.customer_service import CustomerService
from src.services.order_service import OrderService
from src.services.report_service import ReportService
from src.services.backup_service import BackupService

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, db_conn: DatabaseConnection, config, db_path: str = ""):
        super().__init__()
        self._config  = config
        self._db_conn = db_conn
        self._db_path = db_path
        conn = db_conn.get_connection()

        # Repos
        self._customer_repo = CustomerRepository(conn)
        self._order_repo = OrderRepository(conn)
        self._report_repo = ReportRepository(conn)

        # Services
        self._customer_svc = CustomerService(self._customer_repo)
        self._order_svc = OrderService(self._order_repo, self._customer_repo, config)
        self._report_svc = ReportService(self._report_repo, config)
        self._backup_svc = BackupService(db_conn, config._path)

        self.setWindowTitle(f"Διαχείριση Πλυντηρίου — {config.store_name}")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(
            "QFrame#sidebar { background-color: #2c3e50; }"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # App title in sidebar
        title_label = QLabel(f"  Πλυντήριο")
        title_label.setStyleSheet(
            "color: #ecf0f1; font-size: 13pt; font-weight: bold; "
            "padding: 20px 10px 10px 10px;"
        )
        sidebar_layout.addWidget(title_label)

        # Nav buttons
        self._nav_group = QButtonGroup(self)
        self._stack = QStackedWidget()

        nav_items = [
            ("🏠  Πίνακας Ελέγχου", self._create_dashboard),
            ("➕  Νέα Παραγγελία", None),
            ("📋  Παραγγελίες", self._create_orders),
            ("👥  Πελάτες", self._create_customers),
            ("📊  Εκθέσεις", self._create_reports),
            ("⚙️  Ρυθμίσεις", self._create_settings),
        ]

        self._nav_buttons = []
        for i, (label, factory) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(48)
            btn.setStyleSheet(
                "QPushButton { color: #ecf0f1; background: transparent; border: none; "
                "text-align: left; padding: 8px 20px; font-size: 11pt; }"
                "QPushButton:checked { background-color: #3498db; "
                "border-left: 4px solid #ecf0f1; }"
                "QPushButton:hover:!checked { background-color: #34495e; }"
            )
            self._nav_group.addButton(btn, i)
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

            if factory:
                widget = factory()
            else:
                widget = QWidget()  # placeholder for "Νέα Παραγγελία"
            self._stack.addWidget(widget)

        sidebar_layout.addStretch()

        self._nav_group.idClicked.connect(self._on_nav_clicked)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self._stack, 1)

        # Select dashboard by default
        self._nav_buttons[0].setChecked(True)

    def _create_dashboard(self) -> QWidget:
        from src.ui.dashboard_widget import DashboardWidget
        w = DashboardWidget(self._order_svc, self._config)
        w.new_order_requested.connect(self._open_new_order_dialog)
        return w

    def _create_orders(self) -> QWidget:
        from src.ui.order_management_widget import OrderManagementWidget
        w = OrderManagementWidget(self._order_svc, self._config)
        w.new_order_requested.connect(self._open_new_order_dialog)
        return w

    def _create_customers(self) -> QWidget:
        from src.ui.customer_widget import CustomerWidget
        return CustomerWidget(self._customer_svc)

    def _create_reports(self) -> QWidget:
        from src.ui.report_widget import ReportWidget
        return ReportWidget(self._report_svc, self._config)

    def _create_settings(self) -> QWidget:
        from src.ui.settings_widget import SettingsWidget
        return SettingsWidget(self._config,
                              backup_svc=self._backup_svc,
                              db_path=self._db_path)

    @pyqtSlot(int)
    def _on_nav_clicked(self, index: int) -> None:
        if index == 1:
            # "Νέα Παραγγελία" is a dialog, not a stack page
            self._open_new_order_dialog()
            # Re-check the previously checked button
            self._stack.currentWidget()  # no change needed
        else:
            self._stack.setCurrentIndex(index)
            widget = self._stack.currentWidget()
            if hasattr(widget, 'refresh'):
                widget.refresh()

    def _open_new_order_dialog(self) -> None:
        from src.ui.new_order_dialog import NewOrderDialog
        dlg = NewOrderDialog(self._order_svc, self._customer_svc,
                             self._config, self)
        dlg.order_created.connect(self._on_order_created)
        dlg.exec()

    @pyqtSlot(int)
    def _on_order_created(self, order_id: int) -> None:
        logger.info("Παραγγελία δημιουργήθηκε: id=%d", order_id)
        # Refresh dashboard and orders widgets
        for i in [0, 2]:
            w = self._stack.widget(i)
            if hasattr(w, 'refresh'):
                w.refresh()
