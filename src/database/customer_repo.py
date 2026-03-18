# -*- coding: utf-8 -*-
"""
Customer repository — CRUD operations.
"""
import sqlite3
import logging
from src.models.customer import Customer

logger = logging.getLogger(__name__)


class CustomerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, customer: Customer) -> int:
        cursor = self._conn.execute(
            """INSERT INTO customers (name, phone, email, address, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (customer.name, customer.phone, customer.email,
             customer.address, customer.notes)
        )
        self._conn.commit()
        logger.debug("Δημιουργία πελάτη: %s (id=%d)", customer.name, cursor.lastrowid)
        return cursor.lastrowid

    def get_by_id(self, customer_id: int) -> Customer | None:
        row = self._conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        return self._row_to_customer(row) if row else None

    def list_all(self) -> list[Customer]:
        rows = self._conn.execute(
            """SELECT c.*, COUNT(o.id) as order_count
               FROM customers c
               LEFT JOIN orders o ON o.customer_id = c.id
               GROUP BY c.id
               ORDER BY c.name COLLATE NOCASE"""
        ).fetchall()
        return [self._row_to_customer(r) for r in rows]

    def search(self, query: str) -> list[Customer]:
        like = f"%{query}%"
        rows = self._conn.execute(
            """SELECT c.*, COUNT(o.id) as order_count
               FROM customers c
               LEFT JOIN orders o ON o.customer_id = c.id
               WHERE c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?
               GROUP BY c.id
               ORDER BY c.name COLLATE NOCASE""",
            (like, like, like)
        ).fetchall()
        return [self._row_to_customer(r) for r in rows]

    def update(self, customer: Customer) -> None:
        self._conn.execute(
            """UPDATE customers
               SET name=?, phone=?, email=?, address=?, notes=?,
                   updated_at=datetime('now','localtime')
               WHERE id=?""",
            (customer.name, customer.phone, customer.email,
             customer.address, customer.notes, customer.id)
        )
        self._conn.commit()
        logger.debug("Ενημέρωση πελάτη id=%d", customer.id)

    def delete(self, customer_id: int) -> None:
        self._conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        self._conn.commit()
        logger.debug("Διαγραφή πελάτη id=%d", customer_id)

    def has_orders(self, customer_id: int) -> bool:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM orders WHERE customer_id=?", (customer_id,)
        ).fetchone()
        return row[0] > 0

    @staticmethod
    def _row_to_customer(row) -> Customer:
        c = Customer(
            id=row['id'],
            name=row['name'],
            phone=row['phone'] or "",
            email=row['email'] or "",
            address=row['address'] or "",
            notes=row['notes'] or "",
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
        )
        if 'order_count' in row.keys():
            c.order_count = row['order_count']
        return c
