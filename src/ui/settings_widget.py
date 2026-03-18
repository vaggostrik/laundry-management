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
    QDoubleSpinBox, QHeaderView, QFileDialog, QTableWidget,
    QTableWidgetItem, QSizePolicy
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
    def __init__(self, config, backup_svc=None, db_path: str = "", parent=None):
        super().__init__(parent)
        self._config     = config
        self._backup_svc = backup_svc
        self._db_path    = db_path
        self._backup_dir = ""        # remembered between sessions in-memory
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
        tabs.addTab(self._build_backup_tab(), "Αντίγραφα Ασφαλείας")
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

    # ── Backup tab ────────────────────────────────────────────────────────────

    def _build_backup_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        if self._backup_svc is None:
            layout.addWidget(QLabel("Backup service μη διαθέσιμο."))
            layout.addStretch()
            return widget

        # ── Backup folder row ─────────────────────────────────────────────────
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Φάκελος backup:"))
        self._backup_dir_edit = QLineEdit()
        self._backup_dir_edit.setReadOnly(True)
        self._backup_dir_edit.setPlaceholderText("Επιλέξτε φάκελο…")
        folder_layout.addWidget(self._backup_dir_edit)
        browse_btn = QPushButton("Επιλογή…")
        browse_btn.clicked.connect(self._on_browse_backup_dir)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # ── Action buttons ────────────────────────────────────────────────────
        action_layout = QHBoxLayout()

        backup_btn = QPushButton("💾  Δημιουργία Αντιγράφου Τώρα")
        backup_btn.setStyleSheet(
            "QPushButton { background: #3498db; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background: #2980b9; }"
        )
        backup_btn.clicked.connect(self._on_create_backup)
        action_layout.addWidget(backup_btn)

        refresh_btn = QPushButton("🔄  Ανανέωση Λίστας")
        refresh_btn.clicked.connect(self._refresh_backup_list)
        action_layout.addWidget(refresh_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # ── Backup list ───────────────────────────────────────────────────────
        layout.addWidget(QLabel("Αποθηκευμένα αντίγραφα:"))

        self._backup_table = QTableWidget(0, 3)
        self._backup_table.setHorizontalHeaderLabels(
            ["Αρχείο", "Ημερομηνία", "Μέγεθος"])
        self._backup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._backup_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._backup_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)
        self._backup_table.setAlternatingRowColors(True)
        self._backup_table.verticalHeader().setVisible(False)
        self._backup_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self._backup_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._backup_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self._backup_table.itemSelectionChanged.connect(
            self._on_backup_selection_changed)
        layout.addWidget(self._backup_table)

        # ── Restore button ────────────────────────────────────────────────────
        restore_layout = QHBoxLayout()
        self._restore_btn = QPushButton("⚠️  Επαναφορά Επιλεγμένου")
        self._restore_btn.setEnabled(False)
        self._restore_btn.setStyleSheet(
            "QPushButton { background: #e67e22; color: white; border-radius: 4px; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:disabled { background: #bdc3c7; color: white; }"
            "QPushButton:hover:!disabled { background: #d35400; }"
        )
        self._restore_btn.clicked.connect(self._on_restore)
        restore_layout.addWidget(self._restore_btn)
        restore_layout.addStretch()
        layout.addLayout(restore_layout)

        note = QLabel(
            "Μετά την επαναφορά η εφαρμογή πρέπει να επανεκκινηθεί."
        )
        note.setStyleSheet("color: #e74c3c; font-size: 9pt;")
        layout.addWidget(note)

        return widget

    def _on_browse_backup_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Επιλογή Φακέλου Backup",
            self._backup_dir or os.path.expanduser("~")
        )
        if path:
            self._backup_dir = path
            self._backup_dir_edit.setText(path)
            self._refresh_backup_list()

    def _on_create_backup(self) -> None:
        if not self._backup_dir:
            QMessageBox.warning(self, "Προσοχή",
                                "Επιλέξτε πρώτα φάκελο αποθήκευσης.")
            return
        try:
            zip_path = self._backup_svc.create_backup(self._backup_dir)
            self._refresh_backup_list()
            name = os.path.basename(zip_path)
            size = os.path.getsize(zip_path) / 1024
            QMessageBox.information(
                self, "Επιτυχία",
                f"Αντίγραφο ασφαλείας δημιουργήθηκε:\n{name}\n({size:.1f} KB)"
            )
        except Exception as e:
            logger.error("Σφάλμα δημιουργίας backup: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα",
                                 f"Δεν ήταν δυνατή η δημιουργία backup:\n{e}")

    def _refresh_backup_list(self) -> None:
        if not self._backup_dir:
            return
        backups = self._backup_svc.list_backups(self._backup_dir)
        self._backup_table.setRowCount(len(backups))
        for row, b in enumerate(backups):
            self._backup_table.setItem(row, 0, QTableWidgetItem(b['name']))
            self._backup_table.setItem(row, 1, QTableWidgetItem(b['created_at']))
            self._backup_table.setItem(row, 2,
                                       QTableWidgetItem(f"{b['size_kb']:.1f} KB"))
            self._backup_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, b['path'])
        self._on_backup_selection_changed()

    def _on_backup_selection_changed(self) -> None:
        self._restore_btn.setEnabled(
            len(self._backup_table.selectedItems()) > 0)

    def _get_selected_backup_path(self) -> str | None:
        row = self._backup_table.currentRow()
        item = self._backup_table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _on_restore(self) -> None:
        zip_path = self._get_selected_backup_path()
        if not zip_path:
            return
        try:
            info = self._backup_svc.inspect_backup(zip_path)
        except Exception as e:
            QMessageBox.critical(self, "Σφάλμα", f"Μη έγκυρο backup:\n{e}")
            return

        msg = (
            f"Επαναφορά από:\n{os.path.basename(zip_path)}\n\n"
            f"Περιεχόμενο: "
            f"{'βάση δεδομένων' if info['has_db'] else ''}"
            f"{' + ' if info['has_db'] and info['has_config'] else ''}"
            f"{'config.json' if info['has_config'] else ''}\n\n"
            f"⚠️  Τα τρέχοντα δεδομένα θα αντικατασταθούν!\n"
            f"Η εφαρμογή πρέπει να επανεκκινηθεί μετά.\n\n"
            f"Συνέχεια;"
        )
        reply = QMessageBox.question(
            self, "Επιβεβαίωση Επαναφοράς", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            restored = self._backup_svc.restore_backup(zip_path, self._db_path)
            if 'config.json' in restored:
                self._config.reload()
            QMessageBox.information(
                self, "Επαναφορά Ολοκληρώθηκε",
                "Τα δεδομένα επαναφέρθηκαν επιτυχώς.\n\n"
                "Παρακαλώ κλείστε και ανοίξτε ξανά την εφαρμογή."
            )
        except Exception as e:
            logger.error("Σφάλμα επαναφοράς: %s", e, exc_info=True)
            QMessageBox.critical(self, "Σφάλμα",
                                 f"Σφάλμα κατά την επαναφορά:\n{e}")
