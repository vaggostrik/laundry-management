# -*- coding: utf-8 -*-
"""
Database schema initialization — DDL + seeding.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    phone      TEXT,
    email      TEXT,
    address    TEXT,
    notes      TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_name  ON customers(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    status       TEXT    NOT NULL DEFAULT 'received',
    total_amount REAL    NOT NULL DEFAULT 0.0,
    notes        TEXT,
    received_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    ready_at     TEXT,
    delivered_at TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_received_at ON orders(received_at);

CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_key   TEXT    NOT NULL,
    item_name  TEXT    NOT NULL,
    quantity   INTEGER NOT NULL DEFAULT 1,
    unit_price REAL    NOT NULL,
    subtotal   REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def initialize_database(conn: sqlite3.Connection, config=None) -> None:
    cursor = conn.cursor()

    # Execute DDL statements
    for stmt in DDL.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)

    # Schema versioning
    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),)
    )

    # Seed store settings from config if not already present
    if config is not None:
        defaults = {
            'store_name': config.store_name,
            'store_address': config.store_address,
            'store_phone': config.store_phone,
            'store_tax_number': config.store_tax_number,
            'receipt_footer': config.receipt_footer,
        }
        for key, value in defaults.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    conn.commit()
    logger.info("Σχήμα βάσης δεδομένων αρχικοποιήθηκε (έκδοση %d)", SCHEMA_VERSION)
