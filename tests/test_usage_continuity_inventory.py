import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('usage_db_inventory', ROOT / 'tools/usage_continuity_db_inventory.py')
inventory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory_module)


class InventoryTests(unittest.TestCase):
    def test_reads_existing_sqlite_head_including_wal(self):
        with tempfile.TemporaryDirectory(prefix='usage-inventory-') as folder:
            path = Path(folder) / 'ledger.db'
            with sqlite3.connect(path) as db:
                db.execute('PRAGMA journal_mode=WAL')
                db.execute('CREATE TABLE alembic_version (version_num TEXT)')
                db.execute("INSERT INTO alembic_version VALUES ('b234cd56ef78')")
                db.commit()
                result = inventory_module.inventory('sqlite:///' + str(path))
                self.assertEqual(result['alembic_heads'], ['b234cd56ef78'])
                self.assertEqual(result['check'], 'ok')
            db.close()

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory(prefix='usage-inventory-') as folder:
            path = Path(folder) / 'missing.db'
            result = inventory_module.inventory('sqlite:///' + str(path))
            self.assertEqual(result['check'], 'OperationalError')
            self.assertFalse(path.exists())

    def test_non_sqlite_url_never_exposes_credentials(self):
        result = inventory_module.inventory('postgresql://private_user:private_password@example.invalid/secret_db')
        self.assertEqual(result, {'database_engine': 'postgresql', 'check': 'unsupported_database'})
