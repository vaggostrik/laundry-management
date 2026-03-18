# -*- coding: utf-8 -*-
"""
Εργαλείο εκκαθάρισης βάσης δεδομένων.

Διαγράφει ΟΛΕΣ τις εγγραφές από:
  - order_items
  - orders
  - customers

Κρατά ανέπαφα:
  - Σχήμα (tables, indexes)
  - Πίνακα settings (στοιχεία καταστήματος)
  - config.json (τιμοκατάλογος)

Χρήση:
  python clear_database.py              # διαδραστική επιβεβαίωση
  python clear_database.py --yes        # χωρίς ερώτηση (για scripts)
  python clear_database.py --db-path /path/to/laundry.db
"""
import argparse
import os
import sqlite3
import sys


def find_db_path() -> str:
    """Βρίσκει το laundry.db δίπλα στο script."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, 'laundry.db')


def clear_database(db_path: str) -> dict:
    """
    Εκτελεί την εκκαθάριση και επιστρέφει dict με αριθμό διαγραμμένων εγγραφών.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        # Μετρούμε πριν τη διαγραφή
        counts = {}
        for table in ('order_items', 'orders', 'customers'):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0]

        # Διαγραφή με σωστή σειρά (foreign keys)
        conn.execute("DELETE FROM order_items")
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM customers")

        # Επαναφορά autoincrement counters
        for table in ('order_items', 'orders', 'customers'):
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name=?", (table,))

        conn.commit()

        # VACUUM για ανάκτηση χώρου
        conn.execute("VACUUM")
        return counts
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Εκκαθάριση βάσης δεδομένων πλυντηρίου"
    )
    parser.add_argument(
        '--db-path',
        default=None,
        help="Διαδρομή προς το laundry.db (προεπιλογή: δίπλα στο script)"
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help="Παράλειψη επιβεβαίωσης"
    )
    args = parser.parse_args()

    db_path = args.db_path or find_db_path()

    if not os.path.exists(db_path):
        print(f"[ΣΦΑΛΜΑ] Δεν βρέθηκε αρχείο: {db_path}")
        sys.exit(1)

    size_kb = os.path.getsize(db_path) / 1024
    print(f"Βάση δεδομένων : {db_path}")
    print(f"Μέγεθος        : {size_kb:.1f} KB")
    print()

    # Εμφάνιση τρεχόντων εγγραφών
    conn = sqlite3.connect(db_path)
    try:
        rows = {}
        for table in ('customers', 'orders', 'order_items'):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            rows[table] = row[0]
    finally:
        conn.close()

    print("Τρέχουσες εγγραφές:")
    print(f"  Πελάτες      : {rows['customers']}")
    print(f"  Παραγγελίες  : {rows['orders']}")
    print(f"  Είδη παρ/λιών: {rows['order_items']}")
    print()

    if rows['customers'] == 0 and rows['orders'] == 0:
        print("Η βάση είναι ήδη κενή. Δεν χρειάζεται εκκαθάριση.")
        sys.exit(0)

    if not args.yes:
        answer = input(
            "⚠️  ΠΡΟΣΟΧΗ: Θα διαγραφούν ΟΛΕΣ οι εγγραφές.\n"
            "Αυτή η ενέργεια είναι ΜΗ ΑΝΑΣΤΡΕΨΙΜΗ.\n\n"
            "Πληκτρολογήστε  ΝΑΙ  για επιβεβαίωση: "
        ).strip()
        if answer != "ΝΑΙ":
            print("Ακυρώθηκε.")
            sys.exit(0)

    print("\nΕκκαθάριση βάσης…")
    deleted = clear_database(db_path)

    new_size_kb = os.path.getsize(db_path) / 1024
    print()
    print("Διαγράφηκαν:")
    print(f"  Πελάτες      : {deleted['customers']}")
    print(f"  Παραγγελίες  : {deleted['orders']}")
    print(f"  Είδη παρ/λιών: {deleted['order_items']}")
    print()
    print(f"Νέο μέγεθος    : {new_size_kb:.1f} KB")
    print("Η εκκαθάριση ολοκληρώθηκε επιτυχώς.")


if __name__ == '__main__':
    main()
