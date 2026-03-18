# -*- coding: utf-8 -*-
"""
Backup and restore service for the laundry database and config.

Backup format: a .zip file containing:
  - laundry.db   (safe SQLite snapshot via conn.backup())
  - config.json  (pricing + store settings snapshot)

File name:  backup_YYYYMMDD_HHMMSS.zip
"""
import io
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime

logger = logging.getLogger(__name__)

_DB_ENTRY    = "laundry.db"
_CONFIG_ENTRY = "config.json"


class BackupService:
    def __init__(self, db_conn, config_path: str):
        """
        db_conn     — DatabaseConnection instance (provides live sqlite3 conn)
        config_path — absolute path to config.json
        """
        self._db_conn    = db_conn
        self._config_path = config_path

    # ── Backup ────────────────────────────────────────────────────────────────

    def create_backup(self, dest_dir: str) -> str:
        """
        Create a timestamped .zip backup in dest_dir.
        Returns the full path of the created zip file.
        Uses sqlite3.Connection.backup() for a safe, WAL-consistent snapshot.
        """
        os.makedirs(dest_dir, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"backup_{ts}.zip"
        zip_path = os.path.join(dest_dir, zip_name)

        # 1. Dump DB into an in-memory buffer via sqlite3.backup()
        db_buf = io.BytesIO()
        src_conn = self._db_conn.get_connection()
        mem_conn = sqlite3.connect(":memory:")
        src_conn.backup(mem_conn)          # safe, works even with WAL
        # Serialize in-memory DB to bytes
        tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        try:
            tmp_db.close()
            mem_conn.close()
            # Re-open to dump to file
            mem_conn2 = sqlite3.connect(":memory:")
            src_conn.backup(mem_conn2)
            disk_conn = sqlite3.connect(tmp_db.name)
            mem_conn2.backup(disk_conn)
            disk_conn.close()
            mem_conn2.close()

            # 2. Write zip
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(tmp_db.name, _DB_ENTRY)
                if os.path.exists(self._config_path):
                    zf.write(self._config_path, _CONFIG_ENTRY)
        finally:
            try:
                os.unlink(tmp_db.name)
            except OSError:
                pass

        size_kb = os.path.getsize(zip_path) / 1024
        logger.info("Backup δημιουργήθηκε: %s (%.1f KB)", zip_path, size_kb)
        return zip_path

    # ── List backups ──────────────────────────────────────────────────────────

    def list_backups(self, backup_dir: str) -> list[dict]:
        """
        Return list of backup dicts in backup_dir, newest first.
        Each dict: {path, name, size_kb, created_at (str)}
        """
        if not os.path.isdir(backup_dir):
            return []
        results = []
        for fname in os.listdir(backup_dir):
            if not fname.startswith("backup_") or not fname.endswith(".zip"):
                continue
            full = os.path.join(backup_dir, fname)
            try:
                stat = os.stat(full)
                results.append({
                    'path':       full,
                    'name':       fname,
                    'size_kb':    stat.st_size / 1024,
                    'created_at': datetime.fromtimestamp(
                        stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                })
            except OSError:
                continue
        results.sort(key=lambda x: x['created_at'], reverse=True)
        return results

    # ── Restore ───────────────────────────────────────────────────────────────

    def restore_backup(self, zip_path: str, db_path: str) -> list[str]:
        """
        Restore from a backup zip:
          - Replaces the SQLite DB file (db_path) with the one in the zip.
          - Replaces config.json with the one in the zip (if present).

        Returns a list of restored filenames.

        IMPORTANT: the caller must close/reopen the DB connection and
        call Config.reload() after this method returns.
        """
        if not zipfile.is_zipfile(zip_path):
            raise ValueError(f"Το αρχείο δεν είναι έγκυρο backup zip: {zip_path}")

        restored = []
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()

            if _DB_ENTRY in names:
                # Write to a temp file first, then replace atomically
                tmp = db_path + ".restore_tmp"
                with zf.open(_DB_ENTRY) as src, open(tmp, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                # Verify it's a valid SQLite file
                try:
                    test = sqlite3.connect(tmp)
                    test.execute("SELECT name FROM sqlite_master LIMIT 1")
                    test.close()
                except sqlite3.DatabaseError as e:
                    os.unlink(tmp)
                    raise ValueError(
                        f"Η βάση δεδομένων στο backup είναι κατεστραμμένη: {e}")
                shutil.move(tmp, db_path)
                restored.append(_DB_ENTRY)
                logger.info("Επαναφορά DB: %s", db_path)

            if _CONFIG_ENTRY in names:
                with zf.open(_CONFIG_ENTRY) as src, \
                     open(self._config_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                restored.append(_CONFIG_ENTRY)
                logger.info("Επαναφορά config: %s", self._config_path)

        logger.info("Επαναφορά ολοκληρώθηκε από: %s", zip_path)
        return restored

    # ── Inspect zip ───────────────────────────────────────────────────────────

    def inspect_backup(self, zip_path: str) -> dict:
        """Return metadata about a backup zip (for display before restore)."""
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("Μη έγκυρο αρχείο backup")
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            infos = {info.filename: info.file_size for info in zf.infolist()}
        stat = os.stat(zip_path)
        return {
            'has_db':      _DB_ENTRY in names,
            'has_config':  _CONFIG_ENTRY in names,
            'db_size_kb':  infos.get(_DB_ENTRY, 0) / 1024,
            'zip_size_kb': stat.st_size / 1024,
            'created_at':  datetime.fromtimestamp(
                stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
        }
