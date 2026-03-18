# -*- coding: utf-8 -*-
"""
Configuration loader and writer for config.json.
"""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_path: str):
        self._path = config_path
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, encoding='utf-8') as f:
                self._data = json.load(f)
            logger.debug("Φορτώθηκε config από: %s", self._path)
        except FileNotFoundError:
            logger.error("Αρχείο config δεν βρέθηκε: %s", self._path)
            self._data = {}
        except json.JSONDecodeError as e:
            logger.error("Σφάλμα ανάγνωσης config: %s", e)
            self._data = {}

    def reload(self) -> None:
        self._load()

    # ── Store accessors ──────────────────────────────────────────────────────

    @property
    def store_name(self) -> str:
        return self._data.get('store', {}).get('name', 'Πλυντήριο')

    @property
    def store_address(self) -> str:
        return self._data.get('store', {}).get('address', '')

    @property
    def store_phone(self) -> str:
        return self._data.get('store', {}).get('phone', '')

    @property
    def store_tax_number(self) -> str:
        return self._data.get('store', {}).get('tax_number', '')

    @property
    def receipt_footer(self) -> str:
        return self._data.get('store', {}).get('receipt_footer', '')

    @property
    def store_section(self) -> dict:
        return dict(self._data.get('store', {}))

    # ── App accessors ────────────────────────────────────────────────────────

    @property
    def db_path(self) -> str:
        return self._data.get('app', {}).get('db_path', 'laundry.db')

    @property
    def log_level(self) -> str:
        return self._data.get('app', {}).get('log_level', 'INFO')

    @property
    def currency_symbol(self) -> str:
        return self._data.get('app', {}).get('currency_symbol', '€')

    @property
    def date_format(self) -> str:
        return self._data.get('app', {}).get('date_format', '%d/%m/%Y')

    @property
    def datetime_format(self) -> str:
        return self._data.get('app', {}).get('datetime_format', '%d/%m/%Y %H:%M')

    # ── Pricing accessors ────────────────────────────────────────────────────

    @property
    def pricing_categories(self) -> list:
        return self._data.get('pricing', {}).get('categories', [])

    @property
    def service_types(self) -> dict:
        return self._data.get('pricing', {}).get('service_types', {})

    def get_item_price(self, category_key: str, service_key: str) -> float:
        for cat in self.pricing_categories:
            if cat['key'] == category_key:
                svc = cat.get('services', {}).get(service_key)
                if svc:
                    return float(svc['price'])
        return 0.0

    def get_item_label(self, category_key: str, service_key: str) -> str:
        for cat in self.pricing_categories:
            if cat['key'] == category_key:
                svc = cat.get('services', {}).get(service_key)
                if svc:
                    cat_label = cat.get('label', category_key)
                    svc_label = svc.get('label', service_key)
                    return f"{cat_label} - {svc_label}"
        return f"{category_key}/{service_key}"

    def get_category_services(self, category_key: str) -> dict:
        """Returns {service_key: {label, price}} for a given category."""
        for cat in self.pricing_categories:
            if cat['key'] == category_key:
                return cat.get('services', {})
        return {}

    # ── Writers ──────────────────────────────────────────────────────────────

    def write_store_settings(self, data: dict) -> None:
        try:
            self._data['store'] = data
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.info("Αποθηκεύτηκαν ρυθμίσεις καταστήματος")
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης config: %s", e, exc_info=True)
            raise
