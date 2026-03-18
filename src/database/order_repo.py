# -*- coding: utf-8 -*-
"""
Order repository — CRUD + status workflow.
"""
import sqlite3
import logging
from src.models.order import Order, OrderItem
from src.models.enums import OrderStatus

logger = logging.getLogger(__name__)


class OrderRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def create(self, order: Order) -> int:
        cursor = self._conn.execute(
            """INSERT INTO orders (customer_id, status, total_amount, notes)
               VALUES (?, ?, ?, ?)""",
            (order.customer_id, order.status.value,
             order.total_amount, order.notes)
        )
        order_id = cursor.lastrowid
        for item in order.items:
            self._conn.execute(
                """INSERT INTO order_items
                   (order_id, item_key, item_name, quantity, unit_price, subtotal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (order_id, item.item_key, item.item_name,
                 item.quantity, item.unit_price, item.subtotal)
            )
        self._conn.commit()
        logger.debug("Δημιουργία παραγγελίας id=%d για πελάτη id=%d",
                     order_id, order.customer_id)
        return order_id

    def get_by_id(self, order_id: int) -> Order | None:
        row = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE o.id=?""",
            (order_id,)
        ).fetchone()
        if not row:
            return None
        order = self._row_to_order(row)
        order.items = self._get_items(order_id)
        return order

    def list_all(self) -> list[Order]:
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               ORDER BY o.received_at DESC"""
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def list_by_status(self, status: OrderStatus) -> list[Order]:
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE o.status=?
               ORDER BY o.received_at DESC""",
            (status.value,)
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def list_pending(self) -> list[Order]:
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE o.status IN ('received','ready')
               ORDER BY o.received_at DESC"""
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def list_by_date_range(self, start: str, end: str) -> list[Order]:
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE date(o.received_at) BETWEEN date(?) AND date(?)
               ORDER BY o.received_at DESC""",
            (start, end)
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def list_today(self) -> list[Order]:
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE date(o.received_at) = date('now','localtime')
               ORDER BY o.received_at DESC"""
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def search(self, query: str) -> list[Order]:
        like = f"%{query}%"
        rows = self._conn.execute(
            """SELECT o.*, c.name as customer_name
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               WHERE c.name LIKE ? OR CAST(o.id AS TEXT) LIKE ?
               ORDER BY o.received_at DESC""",
            (like, like)
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def update_status(self, order_id: int, new_status: OrderStatus) -> None:
        if new_status == OrderStatus.READY:
            self._conn.execute(
                """UPDATE orders
                   SET status=?, ready_at=datetime('now','localtime'),
                       updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (new_status.value, order_id)
            )
        elif new_status == OrderStatus.DELIVERED:
            self._conn.execute(
                """UPDATE orders
                   SET status=?, delivered_at=datetime('now','localtime'),
                       updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (new_status.value, order_id)
            )
        else:
            self._conn.execute(
                """UPDATE orders
                   SET status=?, updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (new_status.value, order_id)
            )
        self._conn.commit()
        logger.debug("Παραγγελία id=%d → %s", order_id, new_status.value)

    def count_by_status(self, status: OrderStatus) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status=?", (status.value,)
        ).fetchone()
        return row[0]

    def total_revenue_today(self) -> float:
        row = self._conn.execute(
            """SELECT COALESCE(SUM(total_amount), 0)
               FROM orders
               WHERE date(received_at) = date('now','localtime')"""
        ).fetchone()
        return row[0]

    def _get_items(self, order_id: int) -> list[OrderItem]:
        rows = self._conn.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order_id,)
        ).fetchall()
        return [OrderItem(
            id=r['id'],
            order_id=r['order_id'],
            item_key=r['item_key'],
            item_name=r['item_name'],
            quantity=r['quantity'],
            unit_price=r['unit_price'],
            subtotal=r['subtotal'],
        ) for r in rows]

    @staticmethod
    def _row_to_order(row) -> Order:
        return Order(
            id=row['id'],
            customer_id=row['customer_id'],
            customer_name=row['customer_name'],
            status=OrderStatus.from_str(row['status']),
            total_amount=row['total_amount'],
            notes=row['notes'] or "",
            received_at=row['received_at'] or "",
            ready_at=row['ready_at'],
            delivered_at=row['delivered_at'],
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
        )
