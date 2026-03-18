# -*- coding: utf-8 -*-
"""
Customer data model.
"""
from dataclasses import dataclass, field


@dataclass
class Customer:
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""
    order_count: int = 0  # populated by join queries
