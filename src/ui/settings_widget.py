# -*- coding: utf-8 -*-
"""
Settings widget — store info form + interactive pricing catalog CRUD.
"""
import logging
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QTabWidget, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


# ── Dialogs ───────────────────────────────────────────────────────────────────

class CategoryDialog(QDialog):
    """Add or edit a pricing category (key + label)."""

    def __init__(self, key: str = "", label: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Κατηγορία")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._key_edit = QLineEdit(key)
        self._key_edit.setPlaceholderText("π.χ. shirts")
        form.addRow("Key (αγγλικά, χωρίς κενά):", self._key_edit)

        self._label_edit = QLineEdit(label)
        self._label_edit.setPlaceholderText("π.χ. Πουκάμισα")
        form.addRow("Ονομασία:", self._label_edit)

        layout.addLayout(form)

        note = QLabel("Το key χρησιμοποιείται εσωτερικά. Αν το αλλάξετε σε "
                      "υπάρχουσα κατηγορία, νέες παραγγελίες θα χρησιμοποιούν "
                      "το νέο key.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Αποθήκευση")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        key = self._key_edit.text().strip()
        label = self._label_edit.text().strip()
        if not key or not label:
            QMessageBox.warning(self, "Προσοχή", "Συμπληρώστε key και ονομασία.")
            return
        if ' ' in key:
            QMessageBox.warning(self, "Προσοχή",
                                "Το key δεν μπορεί να περιέχει κενά.")
            return
        self.accept()

    def values(self) -> tuple[str, str]:
        return self._key_edit.text().strip(), self._label_edit.text().strip()


class ServiceDialog(QDialog):
    """Add or edit a service (key + label + price)."""

    def __init__(self, svc_key: str = "", label: str = "",
                 price: float = 0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Υπηρεσία")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._key_edit = QLineEdit(svc_key)
        self._key_edit.setPlaceholderText("π.χ. wash_iron")
        form.addRow("Key (αγγλικά, χωρίς κενά):", self._key_edit)

        self._label_edit = QLineEdit(label)
        self._label_edit.setPlaceholderText("π.χ. Πλύσιμο & Σιδέρωμα")
        form.addRow("Ονομασία:", self._label_edit)

        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0.0, 9999.99)
        self._price_spin.setDecimals(2)
        self._price_spin.setSingleStep(0.50)
        self._price_spin.setValue(price)
        self._price_spin.setSuffix(" €")
        form.addRow("Τιμή:", self._price_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Αποθήκευση")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Ακύρωση")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        key = self._key_edit.text().strip()
        label = self._label_edit.text().strip()
        if not key or not label:
            QMessageBox.warning(self, "Προσοχή",
                                "Συμπληρώστε key και ονομασία.")
            return
        if ' ' in key:
            QMessageBox.warning(self, "Προσοχή",
                                "Το key δεν μπορεί να περιέχει κενά.")
            return
        self.accept()

    def values(self) -> tuple[str, str, float]:
        return (self._key_edit.text().strip(),
                self._label_edit.text().strip(),
                self._price_spin.value())


# ── Main widget ───────────────────────────────────────────────────────────────

class SettingsWidget(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Ρυθμίσεις")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_store_tab(), "Στοιχεία Καταστήματος")
        tabs.addTab(self._build_pricing_tab(), "Τιμοκατάλογος")
        layout.addWidget(tabs)

    # ── Store tab ─────────────────────────────────────────────────────────────

    def _build_store_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        store = self._config.store_section

        self._store_name    = QLineEdit(store.get('name', ''))
        self._store_address = QLineEdit(store.get('address', ''))
        self._store_phone   = QLineEdit(store.get('phone', ''))
        self._store_tax     = QLineEdit(store.get('tax_number', ''))
        self._store_footer  = QTextEdit(store.get('receipt_footer', ''))
        self._store_footer.setFixedHeight(60)

        form.addRow("Όνομα Καταστήματος:", self._store_name)
        form.addRow("Διεύθυνση:", self._store_address)
        form.addRow("Τηλέφωνο:", self._store_phone)
        form.addRow("ΑΦΜ:", self._store_tax)
        form.addRow("Κείμενο Απόδειξης:", self._store_footer)

        layout.addLayout(form)
        layout.addSpacing(8)

        save_btn = QPushButton("Αποθήκευση")
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        save_btn.clicked.connect(self._on_save_store)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return widget

    def _on_save_store(self) -> None:
        data = {
            'name':           self._store_name.text().strip(),
            'address':        self._store_address.text().strip(),
            'phone':          self._store_phone.text().strip(),
            'tax_number':     self._store_tax.text().strip(),
            'receipt_footer': self._store_footer.toPlainText().strip(),
        }
        try:
            self._config.write_store_settings(data)
            QMessageBox.information(self, "Επιτυχία",
                                    "Τα στοιχεία καταστήματος αποθηκεύτηκαν.")
        except Exception as e:
            logger.error("Σφάλμα αποθήκευσης ρυθμίσεων: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα αποθήκευσης: {e}")

    # ── Pricing tab ───────────────────────────────────────────────────────────

    def _build_pricing_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()

        self._add_cat_btn = QPushButton("+ Κατηγορία")
        self._add_cat_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 5px 12px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        self._add_cat_btn.clicked.connect(self._on_add_category)
        toolbar.addWidget(self._add_cat_btn)

        self._add_svc_btn = QPushButton("+ Υπηρεσία")
        self._add_svc_btn.setEnabled(False)
        self._add_svc_btn.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; border-radius: 4px; "
            "padding: 5px 12px; font-weight: bold; }"
            "QPushButton:disabled { background: #bdc3c7; color: white; }"
            "QPushButton:hover:!disabled { background: #229954; }"
        )
        self._add_svc_btn.clicked.connect(self._on_add_service)
        toolbar.addWidget(self._add_svc_btn)

        self._edit_btn = QPushButton("✏ Επεξεργασία")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self._edit_btn)

        self._del_btn = QPushButton("🗑 Διαγραφή")
        self._del_btn.setEnabled(False)
        self._del_btn.setStyleSheet(
            "QPushButton { background: #e74c3c; color: white; border-radius: 4px; "
            "padding: 5px 12px; }"
            "QPushButton:disabled { background: #bdc3c7; color: white; }"
            "QPushButton:hover:!disabled { background: #c0392b; }"
        )
        self._del_btn.clicked.connect(self._on_delete)
        toolbar.addWidget(self._del_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tree: 3 columns — Ονομασία | Key | Τιμή
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Ονομασία", "Key", "Τιμή"])
        self._tree.setColumnWidth(0, 260)
        self._tree.setColumnWidth(1, 140)
        self._tree.setColumnWidth(2, 80)
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection)
        layout.addWidget(self._tree)

        self._populate_tree()
        return widget

    def _populate_tree(self) -> None:
        self._tree.clear()
        sym = self._config.currency_symbol
        for cat in self._config.pricing_categories:
            cat_item = QTreeWidgetItem(self._tree, [
                cat['label'], cat['key'], ""
            ])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, ('category', cat['key']))
            f = cat_item.font(0)
            f.setBold(True)
            cat_item.setFont(0, f)
            for svc_key, svc_data in cat.get('services', {}).items():
                svc_item = QTreeWidgetItem(cat_item, [
                    f"  {svc_data['label']}",
                    svc_key,
                    f"{sym}{svc_data['price']:.2f}"
                ])
                svc_item.setData(0, Qt.ItemDataRole.UserRole,
                                 ('service', cat['key'], svc_key))
            cat_item.setExpanded(True)
        self._on_tree_selection()

    def _on_tree_selection(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            self._add_svc_btn.setEnabled(False)
            self._edit_btn.setEnabled(False)
            self._del_btn.setEnabled(False)
            return
        item = items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        is_cat = data and data[0] == 'category'
        is_svc = data and data[0] == 'service'
        self._add_svc_btn.setEnabled(is_cat)
        self._edit_btn.setEnabled(is_cat or is_svc)
        self._del_btn.setEnabled(is_cat or is_svc)

    def _selected_data(self):
        items = self._tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Category actions ──────────────────────────────────────────────────────

    def _on_add_category(self) -> None:
        dlg = CategoryDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        key, label = dlg.values()
        try:
            self._config.add_category(key, label)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα προσθήκης κατηγορίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _on_edit(self) -> None:
        data = self._selected_data()
        if not data:
            return
        if data[0] == 'category':
            self._edit_category(data[1])
        elif data[0] == 'service':
            self._edit_service(data[1], data[2])

    def _edit_category(self, cat_key: str) -> None:
        # Find current label
        label = ""
        for cat in self._config.pricing_categories:
            if cat['key'] == cat_key:
                label = cat['label']
                break
        dlg = CategoryDialog(key=cat_key, label=label, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_key, new_label = dlg.values()
        try:
            self._config.update_category(cat_key, new_key, new_label)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα επεξεργασίας κατηγορίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _on_delete(self) -> None:
        data = self._selected_data()
        if not data:
            return
        if data[0] == 'category':
            self._delete_category(data[1])
        elif data[0] == 'service':
            self._delete_service(data[1], data[2])

    def _delete_category(self, cat_key: str) -> None:
        reply = QMessageBox.question(
            self, "Διαγραφή Κατηγορίας",
            f"Διαγραφή κατηγορίας '{cat_key}' και όλων των υπηρεσιών της;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._config.delete_category(cat_key)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα διαγραφής κατηγορίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    # ── Service actions ───────────────────────────────────────────────────────

    def _on_add_service(self) -> None:
        data = self._selected_data()
        if not data or data[0] != 'category':
            return
        cat_key = data[1]
        dlg = ServiceDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        svc_key, svc_label, price = dlg.values()
        try:
            self._config.add_service(cat_key, svc_key, svc_label, price)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα προσθήκης υπηρεσίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _edit_service(self, cat_key: str, svc_key: str) -> None:
        svcs = self._config.get_category_services(cat_key)
        svc = svcs.get(svc_key, {})
        dlg = ServiceDialog(
            svc_key=svc_key,
            label=svc.get('label', ''),
            price=float(svc.get('price', 0)),
            parent=self
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_key, new_label, new_price = dlg.values()
        try:
            self._config.update_service(cat_key, svc_key, new_key,
                                        new_label, new_price)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα επεξεργασίας υπηρεσίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")

    def _delete_service(self, cat_key: str, svc_key: str) -> None:
        reply = QMessageBox.question(
            self, "Διαγραφή Υπηρεσίας",
            f"Διαγραφή υπηρεσίας '{svc_key}' από την κατηγορία '{cat_key}';",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._config.delete_service(cat_key, svc_key)
            self._populate_tree()
        except ValueError as e:
            QMessageBox.warning(self, "Σφάλμα", str(e))
        except Exception as e:
            logger.error("Σφάλμα διαγραφής υπηρεσίας: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα", f"Σφάλμα: {e}")
