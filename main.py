# -*- coding: utf-8 -*-
"""
Laundry Management Application - Entry Point
"""
import sys
import os


def get_base_dir() -> str:
    """Returns the directory containing config.json and assets/."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir() -> str:
    """Returns the directory for user data (DB, logs) — beside the .exe or beside main.py."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
LOG_PATH = os.path.join(DATA_DIR, 'logs', 'app.log')
DB_PATH_DEFAULT = os.path.join(DATA_DIR, 'laundry.db')

# Ensure logs directory exists before logging is set up
os.makedirs(os.path.join(DATA_DIR, 'logs'), exist_ok=True)

from src.logger import setup_logging
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.schema import initialize_database


def main():
    config = Config(CONFIG_PATH)
    setup_logging(LOG_PATH, config.log_level)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Εκκίνηση εφαρμογής Διαχείρισης Πλυντηρίου")

    db_path = os.path.join(DATA_DIR, config.db_path)
    db_conn = DatabaseConnection(db_path)
    conn = db_conn.get_connection()
    initialize_database(conn, config)
    logger.info("Βάση δεδομένων αρχικοποιήθηκε: %s", db_path)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setApplicationName("Διαχείριση Πλυντηρίου")
    app.setOrganizationName("LaundryApp")

    # Load stylesheet
    qss_path = os.path.join(BASE_DIR, 'assets', 'style.qss')
    if os.path.exists(qss_path):
        with open(qss_path, encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    window = MainWindow(db_conn, config, db_path=db_path)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
