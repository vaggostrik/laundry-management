# -*- coding: utf-8 -*-
"""
Order and OrderItem data models.
"""
from dataclasses import dataclass, field
from src.models.enums import OrderStatus


@dataclass
class OrderItem:
    item_key: str
    item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    id: int | None = None
    order_id: int | None = None


@dataclass
class Order:
    customer_id: int
    status: OrderStatus
    total_amount: float
    notes: str = ""
    id: int | None = None
    customer_name: str = ""
    received_at: str = ""
    ready_at: str | None = None
    delivered_at: str | None = None
    created_at: str = ""
    updated_at: str = ""
    items: list[OrderItem] = field(default_factory=list)
