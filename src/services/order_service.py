# -*- coding: utf-8 -*-
"""
Order business logic — price snapshotting, status transitions.
"""
import logging
from src.models.order import Order, OrderItem
from src.models.enums import OrderStatus
from src.database.order_repo import OrderRepository
from src.database.customer_repo import CustomerRepository

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, order_repo: OrderRepository,
                 customer_repo: CustomerRepository, config):
        self._order_repo = order_repo
        self._customer_repo = customer_repo
        self._config = config

    def create_order(self, customer_id: int,
                     items_data: list[dict],
                     notes: str = "") -> Order:
        """
        items_data: list of {category_key, service_key, quantity}
        Prices are snapshotted from config at order creation time.
        """
        if not items_data:
            raise ValueError("Η παραγγελία πρέπει να περιέχει τουλάχιστον ένα είδος")

        customer = self._customer_repo.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Πελάτης id={customer_id} δεν βρέθηκε")

        order_items = []
        total = 0.0
        for item_data in items_data:
            cat_key = item_data['category_key']
            svc_key = item_data['service_key']
            qty = max(1, int(item_data.get('quantity', 1)))

            price = self._config.get_item_price(cat_key, svc_key)
            label = self._config.get_item_label(cat_key, svc_key)
            subtotal = round(price * qty, 2)
            total += subtotal

            order_items.append(OrderItem(
                item_key=f"{cat_key}/{svc_key}",
                item_name=label,
                quantity=qty,
                unit_price=price,
                subtotal=subtotal,
            ))

        order = Order(
            customer_id=customer_id,
            customer_name=customer.name,
            status=OrderStatus.RECEIVED,
            total_amount=round(total, 2),
            notes=notes.strip(),
            items=order_items,
        )
        order.id = self._order_repo.create(order)
        logger.info("Νέα παραγγελία id=%d για πελάτη '%s', σύνολο=%.2f€",
                    order.id, customer.name, total)
        return order

    def advance_status(self, order_id: int) -> OrderStatus:
        order = self._order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Παραγγελία id={order_id} δεν βρέθηκε")
        next_status = order.status.next_status()
        if next_status is None:
            raise ValueError("Η παραγγελία έχει ήδη παραδοθεί")
        self._order_repo.update_status(order_id, next_status)
        logger.info("Παραγγελία id=%d: %s → %s",
                    order_id, order.status.value, next_status.value)
        return next_status

    def get_order(self, order_id: int) -> Order | None:
        return self._order_repo.get_by_id(order_id)

    def get_all_orders(self) -> list[Order]:
        return self._order_repo.list_all()

    def get_orders_by_status(self, status: OrderStatus) -> list[Order]:
        return self._order_repo.list_by_status(status)

    def get_pending_orders(self) -> list[Order]:
        return self._order_repo.list_pending()

    def get_recent_orders(self, limit: int = 10) -> list[Order]:
        orders = self._order_repo.list_all()
        return orders[:limit]

    def search_orders(self, query: str) -> list[Order]:
        if not query.strip():
            return self._order_repo.list_all()
        return self._order_repo.search(query.strip())

    def count_by_status(self, status: OrderStatus) -> int:
        return self._order_repo.count_by_status(status)

    def revenue_today(self) -> float:
        return self._order_repo.total_revenue_today()

    def count_pending(self) -> int:
        return self._order_repo.count_by_status(OrderStatus.RECEIVED)

    def count_ready(self) -> int:
        return self._order_repo.count_by_status(OrderStatus.READY)
