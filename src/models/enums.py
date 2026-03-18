# -*- coding: utf-8 -*-
"""
Order status enumeration.
"""
from enum import Enum


class OrderStatus(str, Enum):
    RECEIVED  = "received"
    READY     = "ready"
    DELIVERED = "delivered"

    @property
    def greek_label(self) -> str:
        labels = {
            "received":  "Παραλήφθηκε",
            "ready":     "Έτοιμο",
            "delivered": "Παραδόθηκε",
        }
        return labels[self.value]

    def next_status(self) -> "OrderStatus | None":
        transitions = {
            OrderStatus.RECEIVED:  OrderStatus.READY,
            OrderStatus.READY:     OrderStatus.DELIVERED,
            OrderStatus.DELIVERED: None,
        }
        return transitions.get(self)

    @classmethod
    def from_str(cls, value: str) -> "OrderStatus":
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Άγνωστη κατάσταση: {value}")
