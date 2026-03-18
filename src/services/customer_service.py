# -*- coding: utf-8 -*-
"""
Customer business logic.
"""
import logging
from src.models.customer import Customer
from src.database.customer_repo import CustomerRepository

logger = logging.getLogger(__name__)


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository):
        self._repo = customer_repo

    def create_customer(self, name: str, phone: str = "", email: str = "",
                        address: str = "", notes: str = "") -> Customer:
        if not name.strip():
            raise ValueError("Το όνομα πελάτη είναι υποχρεωτικό")
        customer = Customer(
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            notes=notes.strip(),
        )
        customer.id = self._repo.create(customer)
        logger.info("Νέος πελάτης: %s (id=%d)", customer.name, customer.id)
        return customer

    def update_customer(self, customer: Customer) -> None:
        if not customer.name.strip():
            raise ValueError("Το όνομα πελάτη είναι υποχρεωτικό")
        customer.name = customer.name.strip()
        self._repo.update(customer)
        logger.info("Ενημέρωση πελάτη id=%d", customer.id)

    def delete_customer(self, customer_id: int, force: bool = False) -> None:
        if not force and self._repo.has_orders(customer_id):
            raise ValueError(
                "Ο πελάτης έχει παραγγελίες και δεν μπορεί να διαγραφεί. "
                "Επιβεβαιώστε για να συνεχίσετε."
            )
        self._repo.delete(customer_id)
        logger.info("Διαγραφή πελάτη id=%d", customer_id)

    def get_customer(self, customer_id: int) -> Customer | None:
        return self._repo.get_by_id(customer_id)

    def list_customers(self) -> list[Customer]:
        return self._repo.list_all()

    def search_customers(self, query: str) -> list[Customer]:
        if not query.strip():
            return self._repo.list_all()
        return self._repo.search(query.strip())

    def has_orders(self, customer_id: int) -> bool:
        return self._repo.has_orders(customer_id)
